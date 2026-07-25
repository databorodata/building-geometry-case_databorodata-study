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


def _site_record(row: dict[str, Any]) -> SiteRecord:
    return SiteRecord(
        id=row["id"],
        name=row["name"],
        polygon=row["polygon"],
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
