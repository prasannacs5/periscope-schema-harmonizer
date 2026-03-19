"""
Create Vector Search index for historical schema mappings.
Run with:
  CATALOG=... DB_SCHEMA=... WAREHOUSE_ID=... VS_ENDPOINT=... \
  python3 setup/04_create_vs_index.py
"""
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from _env import get_workspace_client, require_vs, CATALOG, SCHEMA, VS_ENDPOINT

from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest,
    EmbeddingSourceColumn,
    PipelineType,
    VectorIndexType,
)

require_vs()

INDEX_NAME = f"{CATALOG}.{SCHEMA}.schema_mappings_index"
SOURCE_TABLE = f"{CATALOG}.{SCHEMA}.approved_mappings"


def main():
    w = get_workspace_client()

    # Check if index already exists
    try:
        existing = w.vector_search_indexes.get_index(INDEX_NAME)
        print(f"✓ Vector Search index already exists: {INDEX_NAME}")
        print(f"  Status: {existing.status.ready}")
        return
    except Exception:
        pass

    print(f"Creating Vector Search index: {INDEX_NAME}")
    print(f"  Source table: {SOURCE_TABLE}")
    print(f"  Endpoint: {VS_ENDPOINT}")

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

    print("  Index creation initiated — polling for READY status...")
    for _ in range(20):
        idx = w.vector_search_indexes.get_index(INDEX_NAME)
        print(f"  Status: {idx.status}")
        if idx.status and idx.status.ready:
            print(f"\n✓ Vector Search index is READY: {INDEX_NAME}")
            break
        time.sleep(15)
    else:
        print("⚠ Index creation still in progress — it will be ready shortly.")


if __name__ == "__main__":
    main()
