"""
Create Lakebase (PostgreSQL) tables for the Periscope Schema Harmonizer.
Run with:
  CATALOG=... DB_SCHEMA=... WAREHOUSE_ID=... \
  PGHOST=<lakebase-host> PGDATABASE=periscope_harmonizer PGUSER=<email> \
  python3 setup/02_create_lakebase_tables.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from _env import (
    get_oauth_token, require_lakebase,
    LAKEBASE_HOST, LAKEBASE_PORT, LAKEBASE_DB, LAKEBASE_USER,
)

import asyncpg

require_lakebase()

DDL = """
-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id     VARCHAR(64) PRIMARY KEY,
    customer_name   VARCHAR(256) NOT NULL,
    industry        VARCHAR(128),
    contact_email   VARCHAR(256),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Upload jobs table (tracks file upload state)
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

-- Schema mappings (proposed + approved)
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

-- Mapping reviews (human decisions)
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

-- Indexes
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
    print("Getting OAuth token...")
    token = get_oauth_token()

    print(f"Connecting to Lakebase at {LAKEBASE_HOST}...")
    conn = await asyncpg.connect(
        host=LAKEBASE_HOST,
        port=LAKEBASE_PORT,
        database=LAKEBASE_DB,
        user=LAKEBASE_USER,
        password=token,
        ssl="require",
    )

    print("Creating tables...")
    raw = [s.strip() for s in DDL.split(";")]
    statements = []
    for s in raw:
        lines = [l for l in s.splitlines() if not l.strip().startswith("--")]
        clean = "\n".join(lines).strip()
        if clean:
            statements.append(clean)

    for stmt in statements:
        try:
            await conn.execute(stmt)
            first_line = stmt.splitlines()[0][:80]
            print(f"  ✓ {first_line}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"  ✓ (already exists): {stmt.splitlines()[0][:60]}")
            else:
                print(f"  ✗ ERROR: {e}")
                raise

    print("\nSeeding customers...")
    await conn.execute(SEED_CUSTOMERS)
    print("  ✓ Inserted 3 demo customers")

    count = await conn.fetchval("SELECT COUNT(*) FROM customers")
    print(f"  ✓ customers table has {count} rows")

    await conn.close()
    print("\n✓ Lakebase tables created and seeded successfully!")


if __name__ == "__main__":
    asyncio.run(setup_lakebase())
