"""LLM-powered schema mapping endpoint using Vector Search for few-shot context."""
import json
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.db import get_db
from server.uc import fetch_rows
from server.llm import chat
from server.config import get_workspace_client, VS_ENDPOINT, VS_INDEX, CATALOG, SCHEMA

router = APIRouter()


class MapSchemaRequest(BaseModel):
    upload_id: str


def get_cdm_fields() -> list[dict]:
    rows = fetch_rows(
        f"SELECT field_name, display_name, data_type, description, example_values "
        f"FROM {CATALOG}.{SCHEMA}.cdm_schema ORDER BY field_id"
    )
    return rows


def search_similar_mappings(source_schema_str: str, num_results: int = 3) -> list[dict]:
    """Query Vector Search for similar historical schema mappings."""
    try:
        w = get_workspace_client()
        results = w.vector_search_indexes.query_index(
            index_name=VS_INDEX,
            query_text=source_schema_str,
            num_results=num_results,
            columns=["mapping_id", "customer_id", "source_schema", "cdm_mapping"],
        )
        if results.result and results.result.data_array:
            cols = [c.name for c in results.result.columns]
            return [dict(zip(cols, row)) for row in results.result.data_array]
    except Exception as e:
        print(f"[VS] Search failed (index may still be provisioning): {e}")
    return []


def build_mapping_prompt(
    source_schema: dict,
    sample_data: list[dict],
    cdm_fields: list[dict],
    similar_mappings: list[dict],
) -> list[dict]:
    cdm_table = "\n".join(
        f"  - {f['field_name']} ({f['data_type']}): {f['description']} | example: {f['example_values']}"
        for f in cdm_fields
    )

    source_cols = "\n".join(
        f"  - {col}: type={info.get('cdm_type') or info.get('type', 'string')}, "
        f"samples={info.get('sample_values', [])[:2]}"
        for col, info in source_schema.items()
    )

    few_shot = ""
    if similar_mappings:
        few_shot = "\n\n## Similar Historical Mappings (use as reference)\n"
        for m in similar_mappings:
            try:
                src = json.loads(m.get("source_schema", "{}"))
                mapping = json.loads(m.get("cdm_mapping", "{}"))
                few_shot += f"\nCustomer {m.get('customer_id', '?')}:\n"
                few_shot += f"  Source cols: {list(src.keys())[:8]}\n"
                few_shot += f"  CDM mapping: {json.dumps(mapping, indent=2)[:400]}\n"
            except Exception:
                pass

    system = """You are a data integration expert for the Periscope GSM platform.
Your job is to map customer sales data schemas to Periscope's Common Data Model (CDM).

Return ONLY valid JSON in exactly this format:
{
  "mappings": [
    {
      "source_column": "original column name",
      "cdm_field": "cdm field name or null if no match",
      "transformation": "expression or null (e.g. 'CAST(x AS DATE)', 'x / 100')",
      "confidence": 0.95,
      "reasoning": "brief explanation"
    }
  ],
  "overall_confidence": 0.87,
  "unmapped_cdm_fields": ["field1", "field2"],
  "notes": "any overall notes about the mapping"
}"""

    user = f"""Map the following customer schema to the Periscope CDM.

## Periscope Common Data Model Fields
{cdm_table}

## Customer Source Schema
{source_cols}

## Sample Data (first 3 rows)
{json.dumps(sample_data[:3], indent=2, default=str)[:1000]}
{few_shot}

Return the JSON mapping. Be precise with column name matching. Use null for cdm_field if no reasonable match exists."""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


@router.post("/map-schema")
async def map_schema(req: MapSchemaRequest):
    """
    Retrieve upload metadata, query VS for similar mappings,
    call LLM to propose CDM mapping, store as pending review.
    """
    pool = await get_db()
    upload = await pool.fetchrow(
        "SELECT * FROM uploads WHERE upload_id = $1", req.upload_id
    )
    if not upload:
        raise HTTPException(404, f"Upload {req.upload_id} not found")

    upload = dict(upload)
    source_schema = json.loads(upload["schema_json"] or "{}")
    sample_data = json.loads(upload["sample_data_json"] or "[]")

    cdm_fields = get_cdm_fields()
    schema_str = " ".join(source_schema.keys())
    similar = search_similar_mappings(schema_str)

    messages = build_mapping_prompt(source_schema, sample_data, cdm_fields, similar)
    llm_response = await chat(messages, temperature=0.1)

    # Parse LLM JSON response
    try:
        # Strip markdown code fences if present
        raw = llm_response.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        mapping_data = json.loads(raw.strip())
    except Exception as e:
        raise HTTPException(500, f"LLM returned invalid JSON: {e}\nRaw: {llm_response[:500]}")

    mapping_id = str(uuid.uuid4())
    similar_ids = [m.get("mapping_id") for m in similar if m.get("mapping_id")]

    await pool.execute(
        """
        INSERT INTO schema_mappings
          (mapping_id, upload_id, customer_id, proposed_at, mapping_json,
           confidence_score, llm_reasoning, similar_mapping_ids, status)
        VALUES ($1, $2, $3, NOW(), $4, $5, $6, $7, 'PENDING')
        """,
        mapping_id,
        req.upload_id,
        upload["customer_id"],
        json.dumps(mapping_data),
        mapping_data.get("overall_confidence", 0.0),
        mapping_data.get("notes", ""),
        json.dumps(similar_ids),
    )

    await pool.execute(
        "UPDATE uploads SET status = 'PENDING_REVIEW' WHERE upload_id = $1",
        req.upload_id,
    )

    return {
        "mapping_id": mapping_id,
        "upload_id": req.upload_id,
        "customer_id": upload["customer_id"],
        "status": "PENDING",
        "mapping": mapping_data,
        "similar_mappings_used": len(similar),
    }


@router.get("/mappings")
async def list_mappings(status: str | None = None):
    pool = await get_db()
    if status:
        rows = await pool.fetch(
            "SELECT * FROM schema_mappings WHERE status = $1 ORDER BY proposed_at DESC",
            status,
        )
    else:
        rows = await pool.fetch(
            "SELECT * FROM schema_mappings ORDER BY proposed_at DESC"
        )
    return [dict(r) for r in rows]


@router.get("/mappings/{mapping_id}")
async def get_mapping(mapping_id: str):
    pool = await get_db()
    row = await pool.fetchrow(
        "SELECT * FROM schema_mappings WHERE mapping_id = $1", mapping_id
    )
    if not row:
        raise HTTPException(404, f"Mapping {mapping_id} not found")
    return dict(row)
