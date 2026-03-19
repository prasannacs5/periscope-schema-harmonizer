"""
Generate synthetic sales data for 3 demo customers with different schemas.
Each customer has POS + CRM data with their own column naming conventions.

Run with:
  CATALOG=... DB_SCHEMA=... WAREHOUSE_ID=... \
  PGHOST=... PGDATABASE=... PGUSER=... \
  python3 setup/03_generate_synthetic_data.py
"""
import asyncio
import json
import uuid
import random
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from _env import (
    get_workspace_client, get_oauth_token, require_lakebase,
    WAREHOUSE_ID, CATALOG, SCHEMA,
    LAKEBASE_HOST, LAKEBASE_PORT, LAKEBASE_DB, LAKEBASE_USER,
)

import asyncpg
from databricks.sdk.service.sql import StatementState
import time

require_lakebase()

# ── Customer schemas (each has unique column names for POS + CRM) ─────────────

CUSTOMERS = {
    "CUST_001": {
        "name": "Carrefour SA",
        "industry": "Retail",
        "pos_schema": {
            "TXN_DATE": ("date", "date"),
            "STORE_CODE": ("store_id", "string"),
            "EAN_CODE": ("product_sku", "string"),
            "PRODUCT_LABEL": ("product_name", "string"),
            "PRODUCT_FAMILY": ("product_category", "string"),
            "SALES_QTY": ("units_sold", "integer"),
            "GROSS_SALES_EUR": ("revenue", "decimal"),
            "PROMO_DISC_EUR": ("discount", "decimal"),
            "NET_SALES_EUR": ("net_revenue", "decimal"),
            "COST_EUR": ("cost", "decimal"),
            "FORMAT": ("channel", "string"),
            "COUNTRY": ("region", "string"),
        },
        "crm_schema": {
            "ORDER_DATE": ("date", "date"),
            "CLIENT_ID": ("customer_id", "string"),
            "CLIENT_NAME": ("customer_name", "string"),
            "ITEM_REF": ("product_sku", "string"),
            "ITEM_NAME": ("product_name", "string"),
            "DEPT": ("product_category", "string"),
            "SOLD_UNITS": ("units_sold", "integer"),
            "TOTAL_REVENUE": ("revenue", "decimal"),
            "DISCOUNT_AMT": ("discount", "decimal"),
            "NET_REVENUE": ("net_revenue", "decimal"),
            "CHANNEL_TYPE": ("channel", "string"),
            "REGION_NAME": ("region", "string"),
            "SALES_REP": ("rep_id", "string"),
        },
    },
    "CUST_002": {
        "name": "Unilever Global",
        "industry": "FMCG",
        "pos_schema": {
            "sale_date": ("date", "date"),
            "outlet_id": ("store_id", "string"),
            "sku_number": ("product_sku", "string"),
            "sku_description": ("product_name", "string"),
            "category_name": ("product_category", "string"),
            "cases_sold": ("units_sold", "integer"),
            "gross_revenue_usd": ("revenue", "decimal"),
            "trade_spend_usd": ("discount", "decimal"),
            "net_revenue_usd": ("net_revenue", "decimal"),
            "cogs_usd": ("cost", "decimal"),
            "trade_channel": ("channel", "string"),
            "market": ("region", "string"),
        },
        "crm_schema": {
            "invoice_date": ("date", "date"),
            "account_number": ("customer_id", "string"),
            "account_name": ("customer_name", "string"),
            "product_code": ("product_sku", "string"),
            "product_desc": ("product_name", "string"),
            "brand_segment": ("product_category", "string"),
            "qty_invoiced": ("units_sold", "integer"),
            "invoice_value": ("revenue", "decimal"),
            "rebate_amount": ("discount", "decimal"),
            "net_sales": ("net_revenue", "decimal"),
            "gp_value": ("margin", "decimal"),
            "go_to_market": ("channel", "string"),
            "territory": ("region", "string"),
            "kam_name": ("rep_id", "string"),
        },
    },
    "CUST_003": {
        "name": "Reckitt Benckiser",
        "industry": "Consumer Goods",
        "pos_schema": {
            "WeekEndDate": ("date", "date"),
            "RetailerCode": ("store_id", "string"),
            "ProductBarcode": ("product_sku", "string"),
            "BrandName": ("product_name", "string"),
            "SubCategory": ("product_category", "string"),
            "VolumeSold": ("units_sold", "integer"),
            "RetailSalesValue": ("revenue", "decimal"),
            "PromotionValue": ("discount", "decimal"),
            "BaselineValue": ("net_revenue", "decimal"),
            "RetailChannel": ("channel", "string"),
            "NielsenMarket": ("region", "string"),
        },
        "crm_schema": {
            "ShipDate": ("date", "date"),
            "CustomerNo": ("customer_id", "string"),
            "CustomerDesc": ("customer_name", "string"),
            "MaterialCode": ("product_sku", "string"),
            "MaterialDesc": ("product_name", "string"),
            "CategoryCode": ("product_category", "string"),
            "ShippedCases": ("units_sold", "integer"),
            "GrossInvoicedSales": ("revenue", "decimal"),
            "DiscountValue": ("discount", "decimal"),
            "NetInvoicedSales": ("net_revenue", "decimal"),
            "CostOfGoods": ("cost", "decimal"),
            "GrossProfit": ("margin", "decimal"),
            "SalesOrg": ("channel", "string"),
            "SalesDistrict": ("region", "string"),
            "SalesRepCode": ("rep_id", "string"),
        },
    },
}

REGIONS = ["EMEA", "North America", "APAC", "LATAM"]
CHANNELS = ["POS", "Online", "B2B", "Wholesale"]
CATEGORIES = ["Health & Beauty", "Food & Beverage", "Home Care", "Personal Care", "Electronics"]


def generate_rows(schema: dict, n: int = 50) -> list[dict]:
    rows = []
    start = date(2024, 1, 1)
    for i in range(n):
        d = start + timedelta(days=random.randint(0, 364))
        row = {}
        for col, (cdm, dtype) in schema.items():
            if dtype == "date":
                row[col] = str(d)
            elif dtype == "integer":
                row[col] = random.randint(10, 500)
            elif dtype == "decimal":
                if cdm == "revenue":
                    val = round(random.uniform(500, 50000), 2)
                elif cdm == "discount":
                    val = round(random.uniform(50, 5000), 2)
                elif cdm in ("net_revenue", "cost"):
                    val = round(random.uniform(400, 45000), 2)
                elif cdm == "margin":
                    val = round(random.uniform(100, 15000), 2)
                else:
                    val = round(random.uniform(100, 10000), 2)
                row[col] = val
            elif cdm == "store_id":
                row[col] = f"STORE_{random.randint(100, 999)}"
            elif cdm == "customer_id":
                row[col] = f"ACC_{random.randint(1000, 9999)}"
            elif cdm == "customer_name":
                names = ["Walmart", "Tesco", "Aldi", "Carrefour", "Lidl", "Kroger"]
                row[col] = random.choice(names)
            elif cdm == "product_sku":
                row[col] = f"SKU-{random.randint(10000, 99999)}"
            elif cdm == "product_name":
                products = ["Dove Soap", "Fairy Liquid", "Surf Excel", "Comfort", "Persil", "Lynx", "Vaseline"]
                row[col] = random.choice(products)
            elif cdm == "product_category":
                row[col] = random.choice(CATEGORIES)
            elif cdm == "channel":
                row[col] = random.choice(CHANNELS)
            elif cdm == "region":
                row[col] = random.choice(REGIONS)
            elif cdm == "rep_id":
                row[col] = f"REP_{random.randint(100, 999)}"
            else:
                row[col] = f"VALUE_{i}"
        rows.append(row)
    return rows


async def insert_uploads_to_lakebase(uploads: list[dict]):
    token = get_oauth_token()
    conn = await asyncpg.connect(
        host=LAKEBASE_HOST, port=LAKEBASE_PORT, database=LAKEBASE_DB,
        user=LAKEBASE_USER, password=token, ssl="require",
    )
    for u in uploads:
        await conn.execute("""
            INSERT INTO uploads
              (upload_id, customer_id, file_name, source_system, row_count, column_count,
               schema_json, sample_data_json, status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'PENDING_MAPPING')
            ON CONFLICT (upload_id) DO NOTHING
        """, u["upload_id"], u["customer_id"], u["file_name"], u["source_system"],
            u["row_count"], u["column_count"], u["schema_json"], u["sample_data_json"])
    await conn.close()
    print(f"  ✓ Inserted {len(uploads)} upload records into Lakebase")


def insert_uploads_to_uc(w, uploads: list[dict]):
    values = []
    for u in uploads:
        schema_esc = u["schema_json"].replace("'", "''")
        sample_esc = u["sample_data_json"].replace("'", "''")
        values.append(
            f"('{u['upload_id']}', '{u['customer_id']}', '{u['customer_name']}', "
            f"'{u['file_name']}', '{u['source_system']}', CURRENT_TIMESTAMP(), "
            f"{u['row_count']}, {u['column_count']}, '{schema_esc}', '{sample_esc}', 'PENDING_REVIEW', NULL)"
        )
    sql = f"""
    INSERT INTO {CATALOG}.{SCHEMA}.raw_uploads
      (upload_id, customer_id, customer_name, file_name, source_system, upload_ts,
       row_count, column_count, schema_json, sample_data_json, status, mapping_id)
    VALUES {','.join(values)}
    """
    resp = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID, statement=sql.strip(), wait_timeout="50s"
    )
    while resp.status.state in (StatementState.PENDING, StatementState.RUNNING):
        time.sleep(3)
        resp = w.statement_execution.get_statement(resp.statement_id)
    if resp.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(f"UC insert failed: {resp.status.error}")
    print(f"  ✓ Inserted {len(uploads)} rows into UC raw_uploads")


def main():
    w = get_workspace_client()
    uploads = []

    for cust_id, cust in CUSTOMERS.items():
        print(f"\nGenerating data for {cust['name']} ({cust_id})...")
        for sys_type, schema in [("POS", cust["pos_schema"]), ("CRM", cust["crm_schema"])]:
            rows = generate_rows(schema, n=50)
            columns = list(schema.keys())
            schema_info = {col: {"type": dtype, "cdm_field": cdm}
                           for col, (cdm, dtype) in schema.items()}
            sample = rows[:3]

            upload = {
                "upload_id": str(uuid.uuid4()),
                "customer_id": cust_id,
                "customer_name": cust["name"],
                "file_name": f"{cust_id.lower()}_{sys_type.lower()}_data_2024.csv",
                "source_system": sys_type,
                "row_count": len(rows),
                "column_count": len(columns),
                "schema_json": json.dumps(schema_info),
                "sample_data_json": json.dumps(sample),
            }
            uploads.append(upload)
            print(f"  ✓ {sys_type}: {len(rows)} rows × {len(columns)} columns")

    print("\nInserting into UC raw_uploads...")
    insert_uploads_to_uc(w, uploads)

    print("Inserting into Lakebase uploads...")
    asyncio.run(insert_uploads_to_lakebase(uploads))

    print(f"\n✓ Synthetic data generation complete!")
    print(f"  Created {len(uploads)} upload records for {len(CUSTOMERS)} customers")


if __name__ == "__main__":
    main()
