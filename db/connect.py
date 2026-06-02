import os
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool, ConnectionPool
from contextlib import asynccontextmanager, contextmanager

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT")
}

CONNINFO = " ".join([f"{k}={v}" for k, v in DB_CONFIG.items()])

# Async connection pool (preferred for new code)
# open=False — pool is opened later by FastAPI lifespan, avoiding
# "no running loop" error at module import time.
async_pool = AsyncConnectionPool(
    conninfo=CONNINFO,
    min_size=2,
    max_size=20,
    timeout=30,
    open=False,
)

# Sync connection pool (for legacy code during migration)
sync_pool = ConnectionPool(
    conninfo=CONNINFO,
    min_size=2,
    max_size=10,
    timeout=30,
    open=True  # Sync pool can open immediately
)

print(f"✅ Database pools initialized")
print(f"   - Async pool (min=2, max=20) - will open on app startup")
print(f"   - Sync pool (min=2, max=10) - ready")


@asynccontextmanager
async def get_async_connection():
    """
    Get an async connection from the pool.

    Usage:
        async with get_async_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT ...")
                result = await cur.fetchone()
            await conn.commit()
    """
    async with async_pool.connection() as conn:
        yield conn


@contextmanager
def get_sync_connection():
    """
    Get a sync connection from the pool (legacy support).

    Usage:
        with get_sync_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT ...")
            result = cur.fetchone()
            conn.commit()
    """
    with sync_pool.connection() as conn:
        yield conn


# Legacy conn object for backward compatibility
class LegacyConnectionWrapper:
    """
    Synchronous connection wrapper for existing code.

    This maintains backward compatibility during migration.
    Uses sync_pool under the hood.
    """

    def __init__(self):
        self._current_conn = None

    def cursor(self, **kwargs):
        from psycopg.rows import dict_row
        if self._current_conn is None:
            self._current_conn = sync_pool.getconn()
        kwargs.setdefault('row_factory', dict_row)
        return self._current_conn.cursor(**kwargs)

    def commit(self):
        if self._current_conn:
            try:
                self._current_conn.commit()
            finally:
                sync_pool.putconn(self._current_conn)
                self._current_conn = None

    def rollback(self):
        if self._current_conn:
            try:
                self._current_conn.rollback()
            finally:
                sync_pool.putconn(self._current_conn)
                self._current_conn = None

    def close(self):
        if self._current_conn:
            sync_pool.putconn(self._current_conn)
            self._current_conn = None

    def __getattr__(self, name):
        if self._current_conn:
            return getattr(self._current_conn, name)
        self._current_conn = sync_pool.getconn()
        return getattr(self._current_conn, name)


# Backward compatibility
conn = LegacyConnectionWrapper()

print("✅ Connected to PostgreSQL successfully!")
