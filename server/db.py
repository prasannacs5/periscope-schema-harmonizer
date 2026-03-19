"""Lakebase (PostgreSQL) connection pool with OAuth token refresh."""
import logging
import os
import time
import asyncpg
from typing import Optional
from server.config import (
    LAKEBASE_HOST, LAKEBASE_PORT, LAKEBASE_DB, LAKEBASE_USER,
    IS_DATABRICKS_APP, get_oauth_token, get_workspace_client, get_workspace_host,
)

logger = logging.getLogger("periscope.db")

# Refresh pool every 45 minutes — Lakebase OAuth tokens expire after ~1 hour
_POOL_TTL_SECONDS = 45 * 60

# Lakebase endpoint path for credential generation
_LB_ENDPOINT_PATH = os.environ.get(
    "LAKEBASE_ENDPOINT_PATH",
    "projects/periscope-harmonizer/branches/production/endpoints/primary",
)


def _generate_database_credential() -> tuple[str, str]:
    """
    Generate a Lakebase database credential via POST /api/2.0/postgres/credentials.

    Returns (user, token) where user is the identity (email or SP applicationId)
    and token is a short-lived database credential.
    """
    import base64
    import json
    import ssl
    import urllib.request

    workspace_host = get_workspace_host().rstrip("/")
    oauth_token = get_oauth_token()

    url = f"{workspace_host}/api/2.0/postgres/credentials"
    body = json.dumps({"endpoint": _LB_ENDPOINT_PATH}).encode()
    print(f"[lakebase] Generating credential via {url}")

    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {oauth_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read())

    db_token = data.get("token", "")
    # Decode the JWT sub claim to get the user identity
    try:
        payload = db_token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        user = claims.get("sub", LAKEBASE_USER)
    except Exception:
        user = LAKEBASE_USER

    print(f"[lakebase] Got credential for user: {user}")
    return user, db_token


def _get_lakebase_credential() -> tuple[str, str]:
    """
    Return (user, password) for Lakebase connection.

    Priority:
    1. PGPASSWORD env var (auto-injected when Lakebase resource is attached)
    2. Generate database credential via postgres credentials API
    3. Workspace OAuth token with resolved identity
    """
    # Resolve user identity
    pg_user = LAKEBASE_USER or os.environ.get("PGUSER", "")
    if not pg_user:
        try:
            w = get_workspace_client()
            pg_user = w.current_user.me().user_name
        except Exception:
            pg_user = ""
    print(f"[lakebase] Resolved user: {pg_user}")

    # 1. Use auto-injected PGPASSWORD
    pg_password = os.environ.get("PGPASSWORD", "")
    if pg_password:
        print(f"[lakebase] Using PGPASSWORD env var")
        return pg_user, pg_password

    # 2. Use workspace OAuth token directly as PG password
    oauth = get_oauth_token()
    print(f"[lakebase] Using workspace OAuth token as PG password")
    return pg_user, oauth


class DatabasePool:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._created_at: float = 0.0

    def _is_stale(self) -> bool:
        return (time.time() - self._created_at) > _POOL_TTL_SECONDS

    async def get_pool(self) -> asyncpg.Pool:
        if self._pool is not None and self._is_stale():
            await self._pool.close()
            self._pool = None

        if self._pool is None:
            user, password = _get_lakebase_credential()
            self._pool = await asyncpg.create_pool(
                host=LAKEBASE_HOST,
                port=LAKEBASE_PORT,
                database=LAKEBASE_DB,
                user=user,
                password=password,
                ssl="require",
                min_size=2,
                max_size=10,
            )
            self._created_at = time.time()
        return self._pool

    async def refresh_token(self):
        """Force-refresh the OAuth token and recreate the pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
        await self.get_pool()

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None


db = DatabasePool()


async def get_db() -> asyncpg.Pool:
    return await db.get_pool()
