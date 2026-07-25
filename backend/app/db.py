from collections.abc import AsyncGenerator
from pathlib import Path
from typing import LiteralString, cast

from fastapi import Request
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from app.config import Config

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def create_pool(config: Config) -> AsyncConnectionPool:
    return AsyncConnectionPool(config.database_url, open=False)


async def apply_schema(pool: AsyncConnectionPool) -> None:
    schema = SCHEMA_PATH.read_text()
    async with pool.connection() as conn:
        for statement in schema.split(";"):
            if statement.strip():
                await conn.execute(cast(LiteralString, statement))


async def get_connection(request: Request) -> AsyncGenerator[AsyncConnection, None]:
    pool: AsyncConnectionPool = request.app.state.db_pool
    async with pool.connection() as conn:
        yield conn
