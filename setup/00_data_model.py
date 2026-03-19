# Databricks notebook source
# MAGIC %md
# MAGIC # Periscope Schema Harmonizer — Data Model Setup
# MAGIC
# MAGIC This notebook creates all infrastructure for the Periscope Schema Harmonizer:
# MAGIC 1. **Unity Catalog** Delta tables (CDM definitions, uploads, approved mappings, ingested sales)
# MAGIC 2. **Lakebase** PostgreSQL tables (transactional workflow state)
# MAGIC 3. **Seed data** (17 CDM fields, 3 demo customers, 6 synthetic uploads)
# MAGIC 4. **Vector Search** index on approved mappings
# MAGIC
# MAGIC ## Storage Architecture
# MAGIC | Layer | Storage | Tables |
# MAGIC |-------|---------|--------|
# MAGIC | CDM & Analytics | Unity Catalog (Delta) | cdm_schema, raw_uploads, ingested_sales, approved_mappings |
# MAGIC | Workflow State | Lakebase (PostgreSQL) | customers, uploads, schema_mappings, mapping_reviews |
# MAGIC | Few-Shot Context | Vector Search | schema_mappings_index (on approved_mappings) |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG = "cfo_eval_demo_catalog"  # Change to your catalog
SCHEMA = "periscope"
VS_ENDPOINT = "periscope-vs-endpoint"

print(f"Target UC: {CATALOG}.{SCHEMA}")
print(f"VS Endpoint: {VS_ENDPOINT}")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 1: Unity Catalog Tables

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Schema

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
print(f"Schema {CATALOG}.{SCHEMA} ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ### cdm_schema
# MAGIC Common Data Model field definitions. Each field represents a canonical column
# MAGIC that customer data gets mapped to.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.cdm_schema (
    field_id        STRING NOT NULL,
    field_name      STRING NOT NULL,
    display_name    STRING NOT NULL,
    data_type       STRING NOT NULL,
    description     STRING,
    is_required     BOOLEAN,
    example_values  STRING,
    added_by        STRING,
    added_at        TIMESTAMP,
    source_customer STRING
)
USING DELTA
COMMENT 'Common Data Model field definitions for Periscope'
""")
print("Created cdm_schema")

# COMMAND ----------

# MAGIC %md
# MAGIC ### raw_uploads
# MAGIC Metadata for uploaded customer files including extracted schema and sample data.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.raw_uploads (
    upload_id        STRING NOT NULL,
    customer_id      STRING NOT NULL,
    customer_name    STRING NOT NULL,
    file_name        STRING NOT NULL,
    source_system    STRING,
    upload_ts        TIMESTAMP,
    row_count        BIGINT,
    column_count     INT,
    schema_json      STRING,
    sample_data_json STRING,
    status           STRING,
    mapping_id       STRING
)
USING DELTA
COMMENT 'Metadata for all uploaded customer sales files'
""")
print("Created raw_uploads")

# COMMAND ----------

# MAGIC %md
# MAGIC ### ingested_sales
# MAGIC Post-approval customer sales data transformed to the CDM schema.
# MAGIC Partitioned by `customer_id` for efficient per-customer queries.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.ingested_sales (
    upload_id        STRING NOT NULL,
    customer_id      STRING NOT NULL,
    sale_date        DATE,
    customer_id_val  STRING,
    customer_name    STRING,
    product_sku      STRING,
    product_name     STRING,
    product_category STRING,
    channel          STRING,
    region           STRING,
    units_sold       BIGINT,
    revenue          DECIMAL(18,2),
    discount         DECIMAL(18,2),
    net_revenue      DECIMAL(18,2),
    cost             DECIMAL(18,2),
    margin           DECIMAL(18,2),
    store_id         STRING,
    rep_id           STRING,
    source_system    STRING,
    ingested_at      TIMESTAMP
)
USING DELTA
PARTITIONED BY (customer_id)
COMMENT 'Post-approval sales data mapped to Periscope CDM'
""")
print("Created ingested_sales")

# COMMAND ----------

# MAGIC %md
# MAGIC ### approved_mappings
# MAGIC Historical approved schema mappings. This table is the source for the Vector Search
# MAGIC index that provides few-shot context to the LLM during mapping generation.
# MAGIC
# MAGIC Change Data Feed is enabled for Delta Sync with Vector Search.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.approved_mappings (
    mapping_id    STRING NOT NULL,
    upload_id     STRING NOT NULL,
    customer_id   STRING NOT NULL,
    source_schema STRING NOT NULL,
    cdm_mapping   STRING NOT NULL,
    approved_by   STRING,
    approved_at   TIMESTAMP
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
COMMENT 'Approved schema mappings used to train Vector Search index'
""")
print("Created approved_mappings")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Seed CDM Fields
# MAGIC 17 standard fields covering date, customer, product, financial, and channel dimensions.

# COMMAND ----------

# Only seed if table is empty
count = spark.sql(f"SELECT COUNT(*) AS cnt FROM {CATALOG}.{SCHEMA}.cdm_schema").collect()[0].cnt
if count == 0:
    spark.sql(f"""
    INSERT INTO {CATALOG}.{SCHEMA}.cdm_schema VALUES
      ('f001', 'date',             'Date',              'DATE',        'Transaction date',                true,  '2024-01-15',           'system', now(), 'system'),
      ('f002', 'customer_id',      'Customer ID',        'STRING',      'Unique customer identifier',      true,  'CUST_001',             'system', now(), 'system'),
      ('f003', 'customer_name',    'Customer Name',      'STRING',      'Customer display name',           false, 'Acme Corp',            'system', now(), 'system'),
      ('f004', 'product_sku',      'Product SKU',        'STRING',      'Product identifier',              true,  'SKU-12345',            'system', now(), 'system'),
      ('f005', 'product_name',     'Product Name',       'STRING',      'Product display name',            false, 'Widget Pro',           'system', now(), 'system'),
      ('f006', 'product_category', 'Product Category',   'STRING',      'Category/segment',                false, 'Electronics',          'system', now(), 'system'),
      ('f007', 'channel',          'Sales Channel',      'STRING',      'Sales channel (POS, online, B2B)',false, 'POS',                  'system', now(), 'system'),
      ('f008', 'region',           'Region',             'STRING',      'Geographic region',               false, 'North America',        'system', now(), 'system'),
      ('f009', 'units_sold',       'Units Sold',         'INTEGER',     'Volume sold',                     true,  '42',                   'system', now(), 'system'),
      ('f010', 'revenue',          'Revenue',            'DECIMAL',     'Gross revenue',                   true,  '1250.00',              'system', now(), 'system'),
      ('f011', 'discount',         'Discount',           'DECIMAL',     'Discount applied',                false, '125.00',               'system', now(), 'system'),
      ('f012', 'net_revenue',      'Net Revenue',        'DECIMAL',     'Revenue after discount',          false, '1125.00',              'system', now(), 'system'),
      ('f013', 'cost',             'Cost',               'DECIMAL',     'Cost of goods sold',              false, '800.00',               'system', now(), 'system'),
      ('f014', 'margin',           'Gross Margin',       'DECIMAL',     'Gross margin (revenue - cost)',   false, '325.00',               'system', now(), 'system'),
      ('f015', 'store_id',         'Store ID',           'STRING',      'Store/location identifier',       false, 'STORE_042',            'system', now(), 'system'),
      ('f016', 'rep_id',           'Sales Rep ID',       'STRING',      'Sales representative identifier', false, 'REP_007',              'system', now(), 'system'),
      ('f017', 'source_system',    'Source System',      'STRING',      'Origin system (POS/CRM/ERP)',     false, 'POS',                  'system', now(), 'system')
    """)
    print("Seeded 17 CDM fields")
else:
    print(f"CDM already has {count} fields, skipping seed")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Verify UC Tables

# COMMAND ----------

tables = spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}").collect()
print(f"Tables in {CATALOG}.{SCHEMA}:")
for t in tables:
    count = spark.sql(f"SELECT COUNT(*) AS cnt FROM {CATALOG}.{SCHEMA}.{t.tableName}").collect()[0].cnt
    print(f"  {t.tableName}: {count} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 2: Lakebase (PostgreSQL) Tables
# MAGIC
# MAGIC These tables handle transactional workflow state: upload tracking, mapping proposals,
# MAGIC human review decisions, and the customer registry.
# MAGIC
# MAGIC **Prerequisites:** A Lakebase Autoscaling project must exist. Set the connection
# MAGIC details below.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Lakebase Connection
# MAGIC Update these values to match your Lakebase project endpoint.

# COMMAND ----------

import subprocess, json

# Auto-detect from Databricks CLI (update PROFILE and PROJECT as needed)
PROFILE = "fe-vm-cfo-eval-demo"
PROJECT = "periscope-harmonizer"
ENDPOINT_PATH = f"projects/{PROJECT}/branches/production/endpoints/primary"

# Get connection details
try:
    r = subprocess.run(['databricks', 'postgres', 'list-endpoints',
        f'projects/{PROJECT}/branches/production',
        '-p', PROFILE, '-o', 'json'], capture_output=True, text=True)
    endpoints = json.loads(r.stdout)
    PGHOST = endpoints[0]['status']['hosts']['host']
    print(f"Lakebase host: {PGHOST}")
except Exception as e:
    PGHOST = ""
    print(f"Could not auto-detect Lakebase host: {e}")
    print("Set PGHOST manually below")

PGPORT = 5432
PGDATABASE = "periscope_harmonizer"

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Tables & Seed Data

# COMMAND ----------

import asyncio
import asyncpg

def get_token():
    r = subprocess.run(['databricks', 'postgres', 'generate-database-credential',
        ENDPOINT_PATH, '-p', PROFILE, '-o', 'json'], capture_output=True, text=True)
    return json.loads(r.stdout)['token']

def get_user():
    r = subprocess.run(['databricks', 'current-user', 'me', '-p', PROFILE, '-o', 'json'],
        capture_output=True, text=True)
    return json.loads(r.stdout)['userName']

DDL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id     VARCHAR(64) PRIMARY KEY,
    customer_name   VARCHAR(256) NOT NULL,
    industry        VARCHAR(128),
    contact_email   VARCHAR(256),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS uploads (
    upload_id       VARCHAR(64) PRIMARY KEY,
    customer_id     VARCHAR(64) NOT NULL REFERENCES customers(customer_id),
    file_name       VARCHAR(512) NOT NULL,
    source_system   VARCHAR(64),
    uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
    row_count       INTEGER,
    column_count    INTEGER,
    schema_json     TEXT,
    sample_data_json TEXT,
    status          VARCHAR(32) DEFAULT 'PENDING_MAPPING'
                    CHECK (status IN ('PENDING_MAPPING','PENDING_REVIEW','APPROVED','REJECTED','INGESTED')),
    error_message   TEXT
);

CREATE TABLE IF NOT EXISTS schema_mappings (
    mapping_id       VARCHAR(64) PRIMARY KEY,
    upload_id        VARCHAR(64) NOT NULL REFERENCES uploads(upload_id),
    customer_id      VARCHAR(64) NOT NULL,
    proposed_at      TIMESTAMPTZ DEFAULT NOW(),
    mapping_json     TEXT NOT NULL,
    confidence_score FLOAT,
    llm_reasoning    TEXT,
    similar_mapping_ids TEXT,
    status           VARCHAR(32) DEFAULT 'PENDING'
                     CHECK (status IN ('PENDING','APPROVED','REJECTED','REVISED'))
);

CREATE TABLE IF NOT EXISTS mapping_reviews (
    review_id       VARCHAR(64) PRIMARY KEY,
    mapping_id      VARCHAR(64) NOT NULL REFERENCES schema_mappings(mapping_id),
    upload_id       VARCHAR(64) NOT NULL,
    reviewer        VARCHAR(256),
    decision        VARCHAR(16) CHECK (decision IN ('APPROVED','REJECTED')),
    reviewed_at     TIMESTAMPTZ DEFAULT NOW(),
    reviewer_notes  TEXT,
    final_mapping_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_uploads_customer ON uploads(customer_id);
CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status);
CREATE INDEX IF NOT EXISTS idx_mappings_upload ON schema_mappings(upload_id);
CREATE INDEX IF NOT EXISTS idx_mappings_status ON schema_mappings(status);
CREATE INDEX IF NOT EXISTS idx_reviews_mapping ON mapping_reviews(mapping_id);
"""

SEED_CUSTOMERS = """
INSERT INTO customers (customer_id, customer_name, industry, contact_email) VALUES
  ('CUST_001', 'Carrefour SA',        'Retail',         'data@carrefour.com'),
  ('CUST_002', 'Unilever Global',     'FMCG',           'analytics@unilever.com'),
  ('CUST_003', 'Reckitt Benckiser',   'Consumer Goods', 'insights@reckitt.com')
ON CONFLICT (customer_id) DO NOTHING;
"""

async def setup_lakebase():
    token = get_token()
    user = get_user()
    print(f"Connecting as {user} to {PGHOST}...")

    conn = await asyncpg.connect(
        host=PGHOST, port=PGPORT, database=PGDATABASE,
        user=user, password=token, ssl="require")

    # Execute DDL
    raw = [s.strip() for s in DDL.split(";")]
    for s in raw:
        lines = [l for l in s.splitlines() if not l.strip().startswith("--")]
        clean = "\n".join(lines).strip()
        if clean:
            try:
                await conn.execute(clean)
                print(f"  ✓ {clean.splitlines()[0][:70]}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"  ✓ (exists) {clean.splitlines()[0][:60]}")
                else:
                    print(f"  ✗ {e}")

    # Seed customers
    await conn.execute(SEED_CUSTOMERS)
    count = await conn.fetchval("SELECT COUNT(*) FROM customers")
    print(f"\n  Customers: {count} rows")

    # Show all tables
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    for t in tables:
        cnt = await conn.fetchval(f"SELECT COUNT(*) FROM {t['tablename']}")
        print(f"  {t['tablename']}: {cnt} rows")

    await conn.close()
    print("\n✓ Lakebase tables ready")

asyncio.run(setup_lakebase())

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Part 3: Vector Search Index
# MAGIC
# MAGIC Creates a Delta Sync index on `approved_mappings` with `databricks-gte-large-en`
# MAGIC embeddings on the `source_schema` column. This powers the few-shot context
# MAGIC retrieval during LLM mapping generation.

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    PipelineType,
    VectorIndexType,
)

w = WorkspaceClient()

INDEX_NAME = f"{CATALOG}.{SCHEMA}.schema_mappings_index"
SOURCE_TABLE = f"{CATALOG}.{SCHEMA}.approved_mappings"

try:
    existing = w.vector_search_indexes.get_index(INDEX_NAME)
    print(f"✓ Index already exists: {INDEX_NAME} (ready={existing.status.ready})")
except Exception:
    print(f"Creating Vector Search index: {INDEX_NAME}")
    w.vector_search_indexes.create_index(
        name=INDEX_NAME,
        endpoint_name=VS_ENDPOINT,
        primary_key="mapping_id",
        index_type=VectorIndexType.DELTA_SYNC,
        delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
            source_table=SOURCE_TABLE,
            pipeline_type=PipelineType.TRIGGERED,
            embedding_source_columns=[
                EmbeddingSourceColumn(
                    name="source_schema",
                    embedding_model_endpoint_name="databricks-gte-large-en",
                )
            ],
        ),
    )
    print("  Index creation initiated — check status in the Vector Search UI")

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Summary
# MAGIC
# MAGIC ### Unity Catalog Tables
# MAGIC | Table | Purpose | Seed Data |
# MAGIC |-------|---------|-----------|
# MAGIC | `cdm_schema` | 17 CDM field definitions | ✓ 17 fields |
# MAGIC | `raw_uploads` | Uploaded file metadata | — |
# MAGIC | `ingested_sales` | Mapped sales data (partitioned by customer) | — |
# MAGIC | `approved_mappings` | Historical mappings for VS indexing (CDF enabled) | — |
# MAGIC
# MAGIC ### Lakebase Tables
# MAGIC | Table | Purpose | Seed Data |
# MAGIC |-------|---------|-----------|
# MAGIC | `customers` | Customer registry | ✓ 3 demo customers |
# MAGIC | `uploads` | Upload tracking & workflow state | — |
# MAGIC | `schema_mappings` | LLM-proposed mappings | — |
# MAGIC | `mapping_reviews` | Human review decisions | — |
# MAGIC
# MAGIC ### Vector Search
# MAGIC | Index | Source | Embedding |
# MAGIC |-------|--------|-----------|
# MAGIC | `schema_mappings_index` | `approved_mappings.source_schema` | `databricks-gte-large-en` |
