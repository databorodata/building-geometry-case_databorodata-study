from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


@dataclass
class SiteRecord:
    id: UUID
    name: str
    polygon: list[Any]
    created_at: datetime


@dataclass
class OptionRecord:
    id: UUID
    site_id: UUID
    parent_id: UUID | None
    source_id: UUID | None
    kind: str
    name: str | None
    params: dict[str, Any]
    result: dict[str, Any]
    created_at: datetime


def _site_record(row: dict[str, Any]) -> SiteRecord:
    return SiteRecord(
        id=row["id"],
        name=row["name"],
        polygon=row["polygon"],
        created_at=row["created_at"],
    )


def _option_record(row: dict[str, Any]) -> OptionRecord:
    return OptionRecord(
        id=row["id"],
        site_id=row["site_id"],
        parent_id=row["parent_id"],
        source_id=row["source_id"],
        kind=row["kind"],
        name=row["name"],
        params=row["params"],
        result=row["result"],
        created_at=row["created_at"],
    )


async def create_site(conn: AsyncConnection, name: str, polygon: list[Any]) -> SiteRecord:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "INSERT INTO sites (id, name, polygon) VALUES (%s, %s, %s) RETURNING id, name, polygon, created_at",
            (uuid4(), name, Jsonb(polygon)),
        )
        row = await cur.fetchone()
    assert row is not None
    return _site_record(row)


async def get_site(conn: AsyncConnection, site_id: UUID) -> SiteRecord | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT id, name, polygon, created_at FROM sites WHERE id = %s",
            (site_id,),
        )
        row = await cur.fetchone()
    return _site_record(row) if row else None


async def list_sites(conn: AsyncConnection) -> list[SiteRecord]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT id, name, polygon, created_at FROM sites ORDER BY created_at, id")
        rows = await cur.fetchall()
    return [_site_record(row) for row in rows]


async def create_option(
    conn: AsyncConnection,
    site_id: UUID,
    parent_id: UUID | None,
    source_id: UUID | None,
    kind: str,
    name: str | None,
    params: dict[str, Any],
    result: dict[str, Any],
) -> OptionRecord:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "INSERT INTO options (id, site_id, parent_id, source_id, kind, name, params, result) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
            "RETURNING id, site_id, parent_id, source_id, kind, name, params, result, created_at",
            (uuid4(), site_id, parent_id, source_id, kind, name, Jsonb(params), Jsonb(result)),
        )
        row = await cur.fetchone()
    assert row is not None
    return _option_record(row)


async def get_option(conn: AsyncConnection, option_id: UUID) -> OptionRecord | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT id, site_id, parent_id, source_id, kind, name, params, result, created_at "
            "FROM options WHERE id = %s",
            (option_id,),
        )
        row = await cur.fetchone()
    return _option_record(row) if row else None


async def list_options(conn: AsyncConnection, site_id: UUID) -> list[OptionRecord]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT id, site_id, parent_id, source_id, kind, name, params, result, created_at FROM options "
            "WHERE site_id = %s ORDER BY created_at, id",
            (site_id,),
        )
        rows = await cur.fetchall()
    return [_option_record(row) for row in rows]
