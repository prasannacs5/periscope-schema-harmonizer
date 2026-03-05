"""Chat interface — Q&A about schema mappings, CDM, and upload history."""
import json
from fastapi import APIRouter
from pydantic import BaseModel
from server.llm import chat
from server.uc import fetch_rows
from server.db import get_db
from server.config import CATALOG, SCHEMA

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    upload_id: str | None = None
    customer_id: str | None = None


def build_context(upload_id: str | None, customer_id: str | None) -> str:
    context_parts = []

    # CDM fields
    cdm = fetch_rows(
        f"SELECT field_name, display_name, data_type, description "
        f"FROM {CATALOG}.{SCHEMA}.cdm_schema ORDER BY field_id"
    )
    cdm_summary = ", ".join(f"{r['field_name']} ({r['data_type']})" for r in cdm)
    context_parts.append(f"CDM fields: {cdm_summary}")

    # Upload context if provided
    if upload_id:
        rows = fetch_rows(
            f"SELECT customer_id, file_name, source_system, row_count, column_count, schema_json "
            f"FROM {CATALOG}.{SCHEMA}.raw_uploads WHERE upload_id = '{upload_id}'"
        )
        if rows:
            u = rows[0]
            context_parts.append(
                f"Current upload: {u['file_name']} from {u['customer_id']} "
                f"({u['source_system']}, {u['row_count']} rows, {u['column_count']} columns)"
            )
            try:
                schema = json.loads(u["schema_json"] or "{}")
                cols = list(schema.keys())
                context_parts.append(f"Source columns: {', '.join(cols)}")
            except Exception:
                pass

    return "\n".join(context_parts)


@router.post("/chat")
async def chat_endpoint(msg: ChatMessage):
    """Answer questions about schema mappings, CDM, and upload history."""
    context = build_context(msg.upload_id, msg.customer_id)

    system = f"""You are a data integration assistant for McKinsey's Periscope platform.
Help analysts understand schema mappings, the Common Data Model, and uploaded customer data.
Be concise and precise. Use technical terminology appropriately.

Context:
{context}"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": msg.message},
    ]

    response = await chat(messages, temperature=0.3, max_tokens=1024)
    return {"response": response, "context_used": bool(context)}


@router.get("/chat/suggestions")
async def get_suggestions(upload_id: str | None = None):
    """Return suggested questions based on current context."""
    if upload_id:
        return {
            "suggestions": [
                "What columns from this file map to revenue?",
                "Which columns couldn't be mapped to the CDM?",
                "Has a similar schema been seen before?",
                "What transformation is needed for the date column?",
                "Show me the confidence scores for each mapping",
            ]
        }
    return {
        "suggestions": [
            "What fields are in the Periscope Common Data Model?",
            "Which customers have uploaded data recently?",
            "How many approved mappings do we have?",
            "What is the CDM definition for net_revenue?",
            "Show me uploads that are pending review",
        ]
    }
