"""Dual-mode auth: works locally (Databricks CLI profile) and in Databricks Apps."""
import os
from databricks.sdk import WorkspaceClient

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))

PROFILE = os.environ.get("DATABRICKS_PROFILE", "")
WAREHOUSE_ID = os.environ.get("WAREHOUSE_ID", "")
CATALOG = os.environ.get("CATALOG", "")
SCHEMA = os.environ.get("DB_SCHEMA", "")
VS_ENDPOINT = os.environ.get("VS_ENDPOINT", "")
VS_INDEX = f"{CATALOG}.{SCHEMA}.schema_mappings_index"
LLM_MODEL = os.environ.get("SERVING_ENDPOINT", "")

LAKEBASE_HOST = os.environ.get("PGHOST", "")
_pgport_raw = os.environ.get("PGPORT", "5432")
try:
    LAKEBASE_PORT = int(_pgport_raw)
except (ValueError, TypeError):
    LAKEBASE_PORT = 5432
LAKEBASE_DB = os.environ.get("PGDATABASE", "")
LAKEBASE_USER = os.environ.get("PGUSER", "")


def get_workspace_client() -> WorkspaceClient:
    if IS_DATABRICKS_APP:
        return WorkspaceClient()
    return WorkspaceClient(profile=PROFILE)


def get_oauth_token() -> str:
    w = get_workspace_client()
    if IS_DATABRICKS_APP:
        host = os.environ.get("DATABRICKS_HOST", "")
        if host and not host.startswith("http"):
            host = f"https://{host}"
        token = os.environ.get("DATABRICKS_TOKEN", "")
        if token:
            return token
    auth_headers = w.config.authenticate()
    return auth_headers["Authorization"].replace("Bearer ", "")


def get_workspace_host() -> str:
    if IS_DATABRICKS_APP:
        host = os.environ.get("DATABRICKS_HOST", "")
        if host and not host.startswith("http"):
            host = f"https://{host}"
        return host
    w = get_workspace_client()
    return w.config.host
