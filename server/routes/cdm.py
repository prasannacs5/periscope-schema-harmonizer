"""CDM Explorer endpoint — browse and understand the Common Data Model."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.uc import fetch_rows, run_sql
from server.config import CATALOG, SCHEMA

router = APIRouter()


@router.get("/cdm")
async def get_cdm():
    """Return all CDM field definitions."""
    rows = fetch_rows(
        f"SELECT * FROM {CATALOG}.{SCHEMA}.cdm_schema ORDER BY field_id"
    )
    return {"fields": rows, "total": len(rows)}


@router.get("/cdm/{field_name}")
async def get_cdm_field(field_name: str):
    """Return a single CDM field definition."""
    rows = fetch_rows(
        f"SELECT * FROM {CATALOG}.{SCHEMA}.cdm_schema "
        f"WHERE field_name = '{field_name}'"
    )
    if not rows:
        raise HTTPException(404, f"CDM field '{field_name}' not found")
    return rows[0]


class NewCDMField(BaseModel):
    field_name: str
    display_name: str
    data_type: str
    description: str
    example_values: str = ""
    is_required: bool = False
    source_customer: str = ""


@router.post("/cdm")
async def add_cdm_field(field: NewCDMField):
    """Add a new field to the CDM (called post-approval when new fields are identified)."""
    existing = fetch_rows(
        f"SELECT field_id FROM {CATALOG}.{SCHEMA}.cdm_schema "
        f"WHERE field_name = '{field.field_name}'"
    )
    if existing:
        raise HTTPException(409, f"Field '{field.field_name}' already exists in CDM")

    # Generate next field_id
    rows = fetch_rows(
        f"SELECT MAX(field_id) AS max_id FROM {CATALOG}.{SCHEMA}.cdm_schema"
    )
    max_id = rows[0]["max_id"] if rows else "f000"
    next_num = int(max_id.replace("f", "")) + 1
    new_id = f"f{next_num:03d}"

    run_sql(f"""
        INSERT INTO {CATALOG}.{SCHEMA}.cdm_schema VALUES (
            '{new_id}',
            '{field.field_name}',
            '{field.display_name}',
            '{field.data_type}',
            '{field.description}',
            {str(field.is_required).lower()},
            '{field.example_values}',
            'user',
            now(),
            '{field.source_customer}'
        )
    """)

    return {
        "field_id": new_id,
        "field_name": field.field_name,
        "message": f"New CDM field '{field.field_name}' added successfully",
    }
