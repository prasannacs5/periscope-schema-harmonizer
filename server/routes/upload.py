"""File upload and schema extraction endpoint."""
import io
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pandas as pd
from server.db import get_db

router = APIRouter()


def extract_schema(df: pd.DataFrame) -> dict:
    """Extract schema metadata from a DataFrame."""
    schema = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        if "int" in dtype:
            cdm_type = "integer"
        elif "float" in dtype:
            cdm_type = "decimal"
        elif "datetime" in dtype or "date" in dtype:
            cdm_type = "date"
        else:
            cdm_type = "string"
        sample = df[col].dropna().head(3).tolist()
        schema[col] = {
            "dtype": dtype,
            "cdm_type": cdm_type,
            "sample_values": [str(s) for s in sample],
            "null_count": int(df[col].isna().sum()),
            "unique_count": int(df[col].nunique()),
        }
    return schema


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    customer_id: str = Form(...),
    source_system: str = Form("UNKNOWN"),
):
    """
    Accept a CSV or Excel file from a customer, extract schema,
    store metadata in Lakebase, return upload_id for tracking.
    """
    filename = file.filename or "upload.csv"
    content = await file.read()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), nrows=200)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content), nrows=200)
        else:
            raise HTTPException(400, "Only CSV and Excel files are supported")
    except Exception as e:
        raise HTTPException(400, f"Could not parse file: {e}")

    schema = extract_schema(df)
    sample_rows = df.head(5).to_dict(orient="records")
    # Sanitise non-serialisable types
    for row in sample_rows:
        for k, v in row.items():
            if not isinstance(v, (str, int, float, bool, type(None))):
                row[k] = str(v)

    upload_id = str(uuid.uuid4())

    pool = await get_db()
    await pool.execute(
        """
        INSERT INTO uploads
          (upload_id, customer_id, file_name, source_system,
           row_count, column_count, schema_json, sample_data_json, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'PENDING_MAPPING')
        """,
        upload_id,
        customer_id,
        filename,
        source_system,
        len(df),
        len(df.columns),
        json.dumps(schema),
        json.dumps(sample_rows),
    )

    return {
        "upload_id": upload_id,
        "customer_id": customer_id,
        "file_name": filename,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "schema": schema,
        "status": "PENDING_MAPPING",
    }


@router.get("/uploads")
async def list_uploads(customer_id: str | None = None):
    """List all uploads, optionally filtered by customer."""
    pool = await get_db()
    if customer_id:
        rows = await pool.fetch(
            "SELECT * FROM uploads WHERE customer_id = $1 ORDER BY uploaded_at DESC",
            customer_id,
        )
    else:
        rows = await pool.fetch("SELECT * FROM uploads ORDER BY uploaded_at DESC")
    return [dict(r) for r in rows]


@router.get("/uploads/{upload_id}")
async def get_upload(upload_id: str):
    pool = await get_db()
    row = await pool.fetchrow("SELECT * FROM uploads WHERE upload_id = $1", upload_id)
    if not row:
        raise HTTPException(404, f"Upload {upload_id} not found")
    return dict(row)
