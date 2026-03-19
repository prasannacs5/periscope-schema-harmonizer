"""
Create Unity Catalog Delta tables for the Periscope Schema Harmonizer.
Run with:
  CATALOG=periscope_harmonizer_catalog DB_SCHEMA=periscope WAREHOUSE_ID=<id> \
  python3 setup/01_create_uc_tables.py
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from _env import get_workspace_client, WAREHOUSE_ID, CATALOG, SCHEMA

from databricks.sdk.service.sql import StatementState

DDL_STATEMENTS = [
    f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}",

    f"""
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
    """,

    f"""
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
    """,

    f"""
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
    """,

    f"""
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
    """,
]

CDM_SEED = f"""
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
"""


def run_sql(w, sql: str, description: str = ""):
    if description:
        print(f"  → {description}")
    resp = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql.strip(),
        wait_timeout="50s",
    )
    while resp.status.state in (StatementState.PENDING, StatementState.RUNNING):
        time.sleep(3)
        resp = w.statement_execution.get_statement(resp.statement_id)
    if resp.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(f"SQL failed: {resp.status.error}")
    return resp


def main():
    w = get_workspace_client()
    print(f"Connected. Running DDL on {CATALOG}.{SCHEMA}...")

    for i, ddl in enumerate(DDL_STATEMENTS, 1):
        first_line = ddl.strip().split("\n")[0].strip()[:80]
        run_sql(w, ddl, f"Step {i}/{len(DDL_STATEMENTS)}: {first_line}")

    print("  → Seeding CDM schema fields...")
    run_sql(w, CDM_SEED, "Inserting 17 CDM field definitions")

    print(f"\n✓ Unity Catalog tables created in {CATALOG}.{SCHEMA}")
    print("  Tables: cdm_schema, raw_uploads, ingested_sales, approved_mappings")


if __name__ == "__main__":
    main()
