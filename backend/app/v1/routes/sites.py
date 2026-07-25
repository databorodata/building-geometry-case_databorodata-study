from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from pydantic import BaseModel

from app import repository
from app.db import get_connection
from app.geometry.polygons import Point
from app.v1.routes.massing import run_massing

router = APIRouter(prefix="/sites", tags=["sites"])


class SiteCreateRequest(BaseModel):
    name: str = "Site"
    polygon: list[Point]


class SiteResponse(BaseModel):
    id: UUID
    name: str
    polygon: list[Point]
    created_at: datetime


def site_polygon(record: repository.SiteRecord) -> list[Point]:
    return [(float(x), float(y)) for x, y in record.polygon]


def site_response(record: repository.SiteRecord) -> SiteResponse:
    return SiteResponse(
        id=record.id,
        name=record.name,
        polygon=site_polygon(record),
        created_at=record.created_at,
    )


@router.post("", status_code=201)
async def create_site(request: SiteCreateRequest, conn: AsyncConnection = Depends(get_connection)) -> SiteResponse:
    run_massing(request.polygon, None)
    site = await repository.create_site(conn, request.name, [list(point) for point in request.polygon])
    return site_response(site)


@router.get("")
async def list_sites(conn: AsyncConnection = Depends(get_connection)) -> list[SiteResponse]:
    records = await repository.list_sites(conn)
    return [site_response(record) for record in records]


@router.get("/{site_id}")
async def get_site(site_id: UUID, conn: AsyncConnection = Depends(get_connection)) -> SiteResponse:
    record = await repository.get_site(conn, site_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site_response(record)
