# Periscope Schema Harmonizer — Demo Script

> Estimated demo time: **8–10 minutes**

---

## Setup Checklist (Before Demo)

- [ ] App is running (locally or deployed to Databricks Apps)
- [ ] 3 demo customers pre-seeded (Carrefour, Unilever, Reckitt)
- [ ] 2 approved mappings pre-loaded in Vector Search (CUST_001 POS + CUST_003 POS)
- [ ] Sample CSV file ready for upload (use `setup/sample_data/` or any CSV with sales columns)
- [ ] Chrome browser open

---

## Act 1: The Problem (1 min)

**Talking points:**
- Periscope ingests sales data from dozens of customers — each with a different schema
- Column names vary wildly: `Revenue`, `gross_rev`, `total_sales`, `amt_sold` all mean the same thing
- Today this mapping is manual, error-prone, and slow — takes days per new customer
- **Goal**: automate schema harmonization with AI while keeping humans in the loop

---

## Act 2: Customer Portal — Upload (2 min)

1. Open the app → lands on **Customer Portal / Upload** page
2. Select a customer from the dropdown (e.g., **Carrefour SA**)
3. Choose source system: **POS**
4. Drag & drop a CSV file (or click to browse)
5. Click **Upload & Extract Schema**

**What to highlight:**
- File is parsed server-side — up to 200 rows sampled
- Schema metadata extracted: column names, inferred types, sample values
- Upload stored in **Lakebase** (PostgreSQL) with status tracking
- Raw file metadata written to **Unity Catalog** Delta table

---

## Act 3: AI Schema Mapping (2 min)

1. After upload completes, click **Map to CDM** on the upload detail page
2. Watch the mapping generate (takes ~3–5 seconds)

**What to highlight:**
- Backend queries **Vector Search** for similar historical mappings (few-shot retrieval)
- Results fed as context to **Claude Sonnet 4.5** via Foundation Model API
- LLM proposes: source_column → cdm_field, transformation, confidence score, reasoning
- Show the mapping results — confidence scores color-coded (green > 0.8, yellow > 0.5, red < 0.5)
- **Key insight**: "Because we already approved a similar Carrefour POS mapping, Vector Search found it and the LLM uses it as a reference — confidence scores are higher"

---

## Act 4: Analyst Review & Approval (2 min)

1. Switch to the **Analyst Portal** (top nav → Analyst)
2. Click on the pending review card
3. Walk through the 3-panel review layout:
   - **Left**: Source schema (customer's columns with sample data)
   - **Center**: Proposed mapping with confidence bars and reasoning
   - **Right**: CDM reference (all 17 standard fields)
4. Optionally edit a mapping (e.g., adjust a transformation expression)
5. Click **Approve**

**What to highlight:**
- Human-in-the-loop — analyst validates before data hits production
- Edits are tracked for audit
- On approval:
  - Data ingested into `ingested_sales` Delta table via CDM mapping
  - Approved mapping stored in `approved_mappings` and synced to **Vector Search**
  - "This approval makes the next similar upload even smarter"

---

## Act 5: Chat Interface (1 min)

1. Switch back to **Customer Portal → Chat**
2. Try a few questions:
   - *"What columns from the latest upload map to revenue?"*
   - *"Has this schema been seen before?"*
   - *"Show me the CDM definition for product_sku"*
3. Show the streaming response

**What to highlight:**
- Context-aware — knows about uploads, mappings, and CDM definitions
- Powered by Claude Sonnet 4.5 with streaming
- Useful for customer self-service and analyst Q&A

---

## Act 6: CDM Explorer (30 sec)

1. Navigate to **Analyst → CDM Explorer**
2. Show the 17 standard CDM fields with types, descriptions, and required flags

**What to highlight:**
- CDM is the canonical schema all customer data maps to
- Extensible — new fields can be proposed when customers bring novel data

---

## Act 7: Architecture Recap (1 min)

Summarize the Databricks components used:

| Component | Role |
|---|---|
| **Databricks Apps** | Hosts the full-stack app (React + FastAPI) |
| **Lakebase** | Transactional state (uploads, reviews, customers) |
| **Vector Search** | Historical mapping retrieval for few-shot LLM context |
| **Foundation Model API** | Claude Sonnet 4.5 for schema mapping + chat |
| **Unity Catalog** | CDM Delta tables, approved mappings, raw uploads |

**Closing point:** "Every approved mapping makes the system smarter. The flywheel effect — more customers, more approved mappings, better AI suggestions, faster onboarding."

---

## Troubleshooting

| Issue | Fix |
|---|---|
| App won't start locally | Check Databricks CLI auth: `databricks auth token --profile fe-vm-periscope-harmonizer` |
| Lakebase connection fails | Verify PGHOST/PGPORT env vars; check Lakebase instance is running |
| LLM mapping returns errors | Confirm `databricks-claude-sonnet-4-5` endpoint is active |
| Vector Search empty results | Run `setup/04_create_vs_index.py` to rebuild the index |
