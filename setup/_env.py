"""
Shared environment config for Periscope Schema Harmonizer setup scripts.
All values are read from environment variables — no hardcoded workspace-specific defaults.

Required env vars:
  DATABRICKS_PROFILE  - CLI profile name (for local execution)
  WAREHOUSE_ID        - SQL warehouse ID
  CATALOG             - Target UC catalog (e.g. 'periscope_harmonizer_catalog')
  DB_SCHEMA           - Target UC schema (e.g. 'periscope')

For Lakebase scripts, also required:
  PGHOST              - Lakebase instance hostname
  PGPORT              - Lakebase port (default: 5432)
  PGDATABASE          - Lakebase database name
  PGUSER              - Lakebase user (email)

For Vector Search scripts:
  VS_ENDPOINT         - Vector Search endpoint name
"""

import os
import sys

from databricks.sdk import WorkspaceClient


def _require(var: str) -> str:
    val = os.environ.get(var)
    if not val:
        print(f"ERROR: Required environment variable {var} is not set.", file=sys.stderr)
        sys.exit(1)
    return val


PROFILE = os.environ.get("DATABRICKS_PROFILE", "")
WAREHOUSE_ID = _require("WAREHOUSE_ID")
CATALOG = _require("CATALOG")
SCHEMA = _require("DB_SCHEMA")

# Lakebase (optional — only needed by scripts 02/03)
LAKEBASE_HOST = os.environ.get("PGHOST", "")
LAKEBASE_PORT = int(os.environ.get("PGPORT", "5432"))
LAKEBASE_DB = os.environ.get("PGDATABASE", "")
LAKEBASE_USER = os.environ.get("PGUSER", "")

# Vector Search (optional — only needed by script 04)
VS_ENDPOINT = os.environ.get("VS_ENDPOINT", "")


def get_workspace_client() -> WorkspaceClient:
    if PROFILE:
        return WorkspaceClient(profile=PROFILE)
    return WorkspaceClient()


def get_oauth_token() -> str:
    w = get_workspace_client()
    auth_headers = w.config.authenticate()
    return auth_headers["Authorization"].replace("Bearer ", "")


def require_lakebase():
    """Validate that Lakebase env vars are set. Call at top of scripts that need them."""
    for var in ("PGHOST", "PGDATABASE", "PGUSER"):
        _require(var)


def require_vs():
    """Validate that Vector Search env vars are set."""
    _require("VS_ENDPOINT")
