"""Snowflake connection pool for the lead-magnet app."""

import asyncio
import queue
import threading
from typing import Any

import snowflake.connector
import structlog

from app.core.settings import settings


logger = structlog.get_logger()


class SnowflakePool:
    """Thread-safe Snowflake connection pool with lazy connection creation."""

    def __init__(self, max_size: int = 3, **connect_kwargs: Any) -> None:  # noqa: ANN401
        self._connect_kwargs = connect_kwargs
        self._pool: queue.Queue[snowflake.connector.SnowflakeConnection] = queue.Queue(
            maxsize=max_size,
        )
        self._max_size = max_size
        self._created = 0
        self._lock = threading.Lock()

    def _create_connection(self) -> snowflake.connector.SnowflakeConnection:
        return snowflake.connector.connect(**self._connect_kwargs)

    def acquire(self) -> snowflake.connector.SnowflakeConnection:
        try:
            conn = self._pool.get_nowait()
        except queue.Empty:
            return self._create_or_wait()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        except Exception:  # noqa: BLE001 — stale connection, replace it
            logger.warning("snowflake_stale_connection")
            with self._lock:
                self._created -= 1
            return self._create_or_wait()
        return conn

    def _create_or_wait(self) -> snowflake.connector.SnowflakeConnection:
        with self._lock:
            if self._created < self._max_size:
                self._created += 1
                return self._create_connection()
        return self._pool.get(timeout=30)

    def release(self, conn: snowflake.connector.SnowflakeConnection) -> None:
        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            logger.warning("snowflake_pool_full", max_size=self._max_size)
            conn.close()
            with self._lock:
                self._created -= 1

    async def execute(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a query in a thread pool and return rows as dicts."""

        def _run() -> list[dict[str, Any]]:
            conn = self.acquire()
            try:
                with conn.cursor(snowflake.connector.DictCursor) as cur:
                    cur.execute(query, params or {})
                    return cur.fetchall()
            except Exception:
                logger.exception("snowflake_query_failed", query=query[:200])
                raise
            finally:
                self.release(conn)

        return await asyncio.to_thread(_run)


_pool: SnowflakePool | None = None


def get_pool() -> SnowflakePool:
    """Return the module-level Snowflake pool, creating it lazily."""
    global _pool  # noqa: PLW0603
    if _pool is None:
        _pool = SnowflakePool(
            max_size=3,
            account=settings.SNOWFLAKE_ACCOUNT,
            user=settings.SNOWFLAKE_USER,
            private_key=settings.SNOWFLAKE_SERIALIZED_KEY,
            role=settings.SNOWFLAKE_ROLE,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
        )
    return _pool
