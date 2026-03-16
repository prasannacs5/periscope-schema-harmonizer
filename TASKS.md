# Periscope Schema Harmonizer — Tasks

## Status Legend
- [ ] Pending
- [x] Completed
- [~] In Progress

---

## Phase 0: Infrastructure

- [x] **0.1** Deploy FE-VM Serverless workspace (`periscope-harmonizer`, us-west-2, 30 days) → `https://fe-sandbox-periscope-harmonizer.cloud.databricks.com`
- [x] **0.2** Authenticate Databricks CLI to FE-VM workspace (`fe-vm-periscope-harmonizer`)
- [x] **0.3** Create Lakebase PostgreSQL instance → `periscope-harmonizer-db` | DNS: `instance-dcc73e40-6699-4763-b3bf-7ce975db83bb.database.cloud.databricks.com`
- [x] **0.4** Create Vector Search endpoint → `periscope-vs-endpoint` (ONLINE)

---

## Phase 1: Data Layer

- [x] **1.1** Create Unity Catalog schema `periscope_harmonizer_catalog.periscope`
- [x] **1.2** Create CDM Delta tables in Unity Catalog
  - `cdm_schema` (17 standard field definitions seeded)
  - `raw_uploads` (uploaded file metadata)
  - `ingested_sales` (post-approval mapped data)
  - `approved_mappings` (mapping history for VS index)
- [x] **1.3** Create Lakebase tables in `periscope_harmonizer` database
  - `customers` (3 demo customers seeded)
  - `uploads` (6 upload records)
  - `schema_mappings`
  - `mapping_reviews`
- [x] **1.4** Create Vector Search index → `schema_mappings_index` (registered, CDF-enabled source table)
- [x] **1.5** Generate synthetic data → 6 uploads (3 customers × POS + CRM, 50 rows each)

---

## Phase 2: Backend (FastAPI)

- [x] **2.1** Scaffold FastAPI project with `uv`, dual-mode auth (`app.py`, `pyproject.toml`, `requirements.txt`, `app.yaml`)
- [x] **2.2** Implement `/api/upload` — parse CSV/Excel, extract schema metadata
- [x] **2.3** Implement `/api/map-schema` — query Vector Search + LLM to propose CDM mapping
- [x] **2.4** Implement `/api/reviews` — list pending / completed reviews
- [x] **2.5** Implement `/api/reviews/decide` — approve/reject mapping, trigger UC ingest + VS sync
- [x] **2.6** Implement `/api/chat` — context-aware Q&A about schema, CDM, history
- [x] **2.7** Implement `/api/cdm` — get/add CDM field definitions
- [x] **2.8** Local test all API endpoints (health, CDM, uploads, map-schema, reviews, chat ✅)

---

## Phase 3: Frontend (React + TypeScript)

- [x] **3.1** Scaffold React/Vite frontend with McKinsey/Periscope brand theme
- [x] **3.2** Build Customer Portal
  - File upload dropzone (CSV/Excel), customer ID + source system
  - Upload history table with status badges
  - Chat interface with suggested questions + context awareness
- [x] **3.3** Build Analyst Review Portal
  - Pending reviews card list with confidence badges
  - 3-panel review detail (source schema | proposed mapping with confidence bars | CDM reference)
  - Approve/Reject with notes textarea
- [x] **3.4** Build CDM Explorer (all 17 fields with types, descriptions, required flags)
- [x] **3.5** Local dev validation — all 7 pages verified with Chrome DevTools MCP
- [x] **3.6** Production build (`npm run build`) — 270KB JS, 27KB CSS ✅

---

## Phase 4: Integration & Local Testing

- [x] **4.1** Vite proxy → FastAPI backend (local dev working)
- [x] **4.2** End-to-end test: upload → LLM mapping → review → approve → CDM ingest ✅
- [x] **4.3** Validate Vector Search retrieval improves mapping accuracy on 2nd similar upload ✅
- [x] **4.4** Test chat interface with 5 sample questions ✅

---

## Phase 5: Deployment

- [x] **5.1** Deploy Databricks App to FE-VM workspace via `databricks apps deploy` ✅
- [x] **5.2** Attach Lakebase instance to app via UI (resource key: `database`) ✅
- [x] **5.3** Attach Foundation Model serving endpoint to app (`databricks-claude-sonnet-4-5`) ✅
- [x] **5.4** Smoke test deployed app in Chrome ✅
- [x] **5.5** Validate /logz app logs, fix any startup issues ✅ (fixed PGPORT crash + UC permissions)

---

## Phase 6: Demo Polish

- [x] **6.1** Pre-load 2 approved mappings in Vector Search (simulate prior history) ✅ (CUST_001 POS + CUST_003 POS synced)
- [x] **6.2** Create demo script / walkthrough notes ✅ (docs/DEMO_SCRIPT.md)
- [x] **6.3** Final screenshot / recording of full flow ✅ (6 screenshots in docs/screenshots/, email draft in docs/EMAIL_DRAFT.md)
