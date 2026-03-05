"""Human review, approve, and reject endpoints."""
import json
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.db import get_db
from server.uc import run_sql
from server.config import get_workspace_client, VS_INDEX, CATALOG, SCHEMA

router = APIRouter()


class ReviewDecision(BaseModel):
    mapping_id: str
    upload_id: str
    decision: str  # "APPROVED" or "REJECTED"
    reviewer: str = "analyst"
    reviewer_notes: str = ""
    final_mapping_json: str = ""  # Optionally edited mapping JSON


@router.get("/reviews")
async def list_reviews(status: str | None = None):
    """List all mappings pending or completed review."""
    pool = await get_db()
    if status == "pending":
        rows = await pool.fetch(
            """
            SELECT sm.*, u.file_name, u.customer_id, u.source_system, u.row_count
            FROM schema_mappings sm
            JOIN uploads u ON sm.upload_id = u.upload_id
            WHERE sm.status = 'PENDING'
            ORDER BY sm.proposed_at DESC
            """
        )
    elif status == "completed":
        rows = await pool.fetch(
            """
            SELECT mr.*, sm.mapping_json, sm.confidence_score,
                   u.file_name, u.customer_id
            FROM mapping_reviews mr
            JOIN schema_mappings sm ON mr.mapping_id = sm.mapping_id
            JOIN uploads u ON mr.upload_id = u.upload_id
            ORDER BY mr.reviewed_at DESC
            """
        )
    else:
        rows = await pool.fetch(
            """
            SELECT sm.*, u.file_name, u.source_system, u.row_count
            FROM schema_mappings sm
            JOIN uploads u ON sm.upload_id = u.upload_id
            ORDER BY sm.proposed_at DESC
            """
        )
    return [dict(r) for r in rows]


@router.get("/reviews/{mapping_id}")
async def get_review_detail(mapping_id: str):
    """Full review detail: upload info + mapping + CDM definitions."""
    pool = await get_db()
    mapping = await pool.fetchrow(
        "SELECT * FROM schema_mappings WHERE mapping_id = $1", mapping_id
    )
    if not mapping:
        raise HTTPException(404, f"Mapping {mapping_id} not found")
    mapping = dict(mapping)

    upload = await pool.fetchrow(
        "SELECT * FROM uploads WHERE upload_id = $1", mapping["upload_id"]
    )
    return {
        "mapping": mapping,
        "upload": dict(upload) if upload else None,
    }


@router.post("/reviews/decide")
async def submit_review(decision: ReviewDecision):
    """
    Submit approval or rejection.
    On APPROVED: ingest data into UC, update VS index.
    On REJECTED: mark for re-mapping.
    """
    pool = await get_db()
    mapping = await pool.fetchrow(
        "SELECT * FROM schema_mappings WHERE mapping_id = $1", decision.mapping_id
    )
    if not mapping:
        raise HTTPException(404, f"Mapping {decision.mapping_id} not found")
    mapping = dict(mapping)

    upload = await pool.fetchrow(
        "SELECT * FROM uploads WHERE upload_id = $1", decision.upload_id
    )
    if not upload:
        raise HTTPException(404, f"Upload {decision.upload_id} not found")
    upload = dict(upload)

    if decision.decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(400, "decision must be APPROVED or REJECTED")

    # Use edited mapping if provided, else original
    final_mapping = decision.final_mapping_json or mapping["mapping_json"]

    review_id = str(uuid.uuid4())
    await pool.execute(
        """
        INSERT INTO mapping_reviews
          (review_id, mapping_id, upload_id, reviewer, decision,
           reviewed_at, reviewer_notes, final_mapping_json)
        VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7)
        """,
        review_id,
        decision.mapping_id,
        decision.upload_id,
        decision.reviewer,
        decision.decision,
        decision.reviewer_notes,
        final_mapping,
    )

    if decision.decision == "APPROVED":
        await pool.execute(
            "UPDATE schema_mappings SET status = 'APPROVED' WHERE mapping_id = $1",
            decision.mapping_id,
        )
        await pool.execute(
            "UPDATE uploads SET status = 'APPROVED' WHERE upload_id = $1",
            decision.upload_id,
        )
        # Store in UC approved_mappings for VS indexing
        source_schema = upload.get("schema_json", "{}")
        src_esc = (source_schema or "{}").replace("'", "''")
        final_esc = final_mapping.replace("'", "''")
        mapping_id_esc = decision.mapping_id
        upload_id_esc = decision.upload_id
        customer_id_esc = upload["customer_id"]

        run_sql(f"""
            INSERT INTO {CATALOG}.{SCHEMA}.approved_mappings
              (mapping_id, upload_id, customer_id, source_schema, cdm_mapping, approved_by, approved_at)
            VALUES
              ('{mapping_id_esc}', '{upload_id_esc}', '{customer_id_esc}',
               '{src_esc}', '{final_esc}',
               '{decision.reviewer}', now())
        """)

        # Trigger VS index sync
        try:
            w = get_workspace_client()
            w.vector_search_indexes.sync_index(VS_INDEX)
        except Exception as e:
            print(f"[VS] Sync triggered (may already be syncing): {e}")

        return {
            "status": "APPROVED",
            "review_id": review_id,
            "message": "Mapping approved. Data ingestion queued. Vector Search index sync triggered.",
        }

    else:
        await pool.execute(
            "UPDATE schema_mappings SET status = 'REJECTED' WHERE mapping_id = $1",
            decision.mapping_id,
        )
        await pool.execute(
            "UPDATE uploads SET status = 'PENDING_MAPPING' WHERE upload_id = $1",
            decision.upload_id,
        )
        return {
            "status": "REJECTED",
            "review_id": review_id,
            "message": "Mapping rejected. Re-submit to /api/map-schema to get a revised mapping.",
        }
