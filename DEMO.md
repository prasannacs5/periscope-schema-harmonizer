# Periscope Schema Harmonizer — Demo

## Overview

A feature enhancement for **McKinsey Periscope** (GSM Practice) that enables customers to upload proprietary sales data (POS, CRM, etc.) through a branded customer-facing portal. The system uses an LLM + Vector Search to intelligently map the customer's schema to Periscope's **Common Data Model (CDM)**, routes proposed mappings through a **human review workflow**, and enriches the CDM post-approval.

---

## Brand Guidelines

### McKinsey / Periscope Brand

| Token | Value |
|-------|-------|
| Primary Blue | `#005eb8` |
| Dark Navy | `#24477f` |
| Periscope Slate | `#52677b` |
| Background | `#f5f5f5` |
| Text Dark | `#222222` |
| Gray | `#a2aaad` |
| Accent Gold | `#f3c13a` |
| White | `#ffffff` |

- **Font**: Inter (system fallback: sans-serif)
- **Style**: Clean, corporate, data-dense. Card-based UI. Subtle shadows. No gradients.
- **Logo**: "Periscope | Powered by Databricks" wordmark in top-left header.

---

## Use Cases Built Into This Demo

### UC1 — Customer Data Upload & Schema Extraction
Customers log into the Periscope portal and upload a spreadsheet (CSV or Excel) containing sales data. The system parses the file, extracts column names, sample values, and infers data types.

### UC2 — LLM-Powered Schema Mapping with Vector Search
The system queries a Vector Search index for historically approved mappings from similar customer schemas. The LLM uses these as few-shot examples to propose a mapping from the customer's schema to the Periscope CDM. Each mapping includes:
- Source column → Target CDM field
- Transformation expression (if needed)
- Confidence score
- Reasoning

### UC3 — Human Review & Approval Workflow
A Periscope analyst (human reviewer) sees a side-by-side view of:
- Customer schema on the left
- Proposed CDM mapping on the right
- Confidence scores and reasoning
The reviewer can edit individual mappings, approve the full set, or reject with feedback.

### UC4 — CDM Enhancement & Vector Search Update
Post-approval, the system:
- Applies the mapping to ingest the customer's data into the CDM Delta tables
- Stores the approved mapping in Vector Search for future reuse
- Updates the CDM schema if new fields are introduced

### UC5 — Chat Interface
A conversational UI allows users to ask questions like:
- "What columns from this file map to revenue?"
- "Has this schema been seen before?"
- "Show me the CDM definition for product_sku"

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               Periscope Schema Harmonizer App               │
│                   (Databricks App)                          │
├──────────────────────────┬──────────────────────────────────┤
│   Customer Portal (React)│   Analyst Review Portal (React)  │
│   - File upload          │   - Side-by-side mapping review  │
│   - Upload history       │   - Approve / Edit / Reject      │
│   - Chat interface       │   - Mapping audit trail          │
└──────────┬───────────────┴──────────────┬───────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  /api/upload        /api/map-schema    /api/reviews          │
│  /api/approve       /api/reject        /api/chat             │
└─────────┬──────────────────┬──────────────┬─────────────────┘
          │                  │              │
          ▼                  ▼              ▼
┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐
│   Lakebase   │  │  Vector Search   │  │  Foundation Model  │
│  (PostgreSQL)│  │  (schema index)  │  │  Claude Sonnet 4.5 │
│              │  │                  │  │                    │
│ - customers  │  │ Historical       │  │ Schema mapping     │
│ - uploads    │  │ schema mappings  │  │ Chat Q&A           │
│ - mappings   │  │ as embeddings    │  │                    │
│ - reviews    │  │                  │  │                    │
└──────────────┘  └──────────────────┘  └────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────┐
│          Unity Catalog (Delta Tables)            │
│  <catalog>.periscope.common_data_model           │
│  <catalog>.periscope.raw_uploads                 │
│  <catalog>.periscope.ingested_sales              │
└──────────────────────────────────────────────────┘
```

---

## Common Data Model (CDM) — Periscope Standard Fields

| CDM Field | Type | Description |
|-----------|------|-------------|
| `date` | DATE | Transaction date |
| `customer_id` | STRING | Unique customer identifier |
| `customer_name` | STRING | Customer display name |
| `product_sku` | STRING | Product identifier |
| `product_name` | STRING | Product display name |
| `product_category` | STRING | Category/segment |
| `channel` | STRING | Sales channel (POS, online, B2B) |
| `region` | STRING | Geographic region |
| `units_sold` | INTEGER | Volume sold |
| `revenue` | DECIMAL | Gross revenue |
| `discount` | DECIMAL | Discount applied |
| `net_revenue` | DECIMAL | Revenue after discount |
| `cost` | DECIMAL | Cost of goods sold |
| `margin` | DECIMAL | Gross margin |
| `store_id` | STRING | Store/location identifier |
| `rep_id` | STRING | Sales rep identifier |
| `source_system` | STRING | Origin system (POS/CRM/ERP) |

---

## Databricks Features Exercised

- **Databricks Apps** — Customer-facing portal + analyst review portal
- **Lakebase** — State management (uploads, reviews, approval workflow)
- **Vector Search** — Historical schema mapping retrieval (few-shot context for LLM)
- **Foundation Model API** — Claude Sonnet 4.5 for schema mapping + chat
- **Unity Catalog** — CDM Delta tables with 3-layer namespaces
- **Serverless Compute** — Data ingestion and schema processing jobs

---

## Workspace

- **Type**: FE-VM Serverless (required for Apps + Lakebase + Vector Search)
- **Region**: us-west-2
- **Profile**: fe-vm-periscope-harmonizer
