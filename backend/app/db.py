"""Подключение к Postgres: пул соединений, применение схемы, FastAPI-зависимость."""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import LiteralString, cast

from fastapi import Request
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from app.config import Config

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def create_pool(config: Config) -> AsyncConnectionPool:
    """Создаёт пул, не открывая его: в сеть ходим в lifespan, а не на импорте модуля."""
    return AsyncConnectionPool(config.database_url, open=False)


async def apply_schema(pool: AsyncConnectionPool) -> None:
    """Применяет schema.sql при старте — наши миграции.

    Файл режется по «;» (psycopg 3 не принимает несколько команд в одном execute);
    благодаря IF NOT EXISTS в схеме вызов идемпотентен. cast(LiteralString) — типизация
    psycopg требует литеральных строк; наш SQL из своего файла пакета — безопасен.
    """
    schema = SCHEMA_PATH.read_text()
    async with pool.connection() as conn:
        for statement in schema.split(";"):
            if statement.strip():
                await conn.execute(cast(LiteralString, statement))


async def get_connection(request: Request) -> AsyncGenerator[AsyncConnection, None]:
    """FastAPI-зависимость: соединение из пула на время запроса, возврат — автоматом."""
    pool: AsyncConnectionPool = request.app.state.db_pool
    async with pool.connection() as conn:
        yield conn
