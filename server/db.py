"""Lakebase (PostgreSQL) connection pool with OAuth token refresh."""
import time
import asyncpg
from typing import Optional
from server.config import (
    LAKEBASE_HOST, LAKEBASE_PORT, LAKEBASE_DB, LAKEBASE_USER, get_oauth_token
)

# Refresh pool every 45 minutes — Lakebase OAuth tokens expire after ~1 hour
_POOL_TTL_SECONDS = 45 * 60


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
            token = get_oauth_token()
            self._pool = await asyncpg.create_pool(
                host=LAKEBASE_HOST,
                port=LAKEBASE_PORT,
                database=LAKEBASE_DB,
                user=LAKEBASE_USER,
                password=token,
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
