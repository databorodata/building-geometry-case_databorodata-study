from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from pydantic import BaseModel

from app import repository
from app.db import get_connection
from app.geometry.massing import MassingParams, MassingResult
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


class OptionResponse(BaseModel):
    id: UUID
    site_id: UUID
    parent_id: UUID | None
    kind: str
    name: str | None
    params: MassingParams
    result: MassingResult
    created_at: datetime


class SiteCreateResponse(BaseModel):
    site: SiteResponse
    root_option: OptionResponse


class OptionCreateRequest(BaseModel):
    parent_id: UUID
    kind: Literal["save", "fork"] = "save"
    name: str | None = None
    params: MassingParams


def site_polygon(record: repository.SiteRecord) -> list[Point]:
    return [(float(x), float(y)) for x, y in record.polygon]


def site_response(record: repository.SiteRecord) -> SiteResponse:
    return SiteResponse(
        id=record.id,
        name=record.name,
        polygon=site_polygon(record),
        created_at=record.created_at,
    )


def option_response(record: repository.OptionRecord) -> OptionResponse:
    return OptionResponse(
        id=record.id,
        site_id=record.site_id,
        parent_id=record.parent_id,
        kind=record.kind,
        name=record.name,
        params=MassingParams.model_validate(record.params),
        result=MassingResult.model_validate(record.result),
        created_at=record.created_at,
    )


@router.post("", status_code=201)
async def create_site(
    request: SiteCreateRequest, conn: AsyncConnection = Depends(get_connection)
) -> SiteCreateResponse:
    params, result = run_massing(request.polygon, None)
    site = await repository.create_site(conn, request.name, [list(point) for point in request.polygon])
    option = await repository.create_option(conn, site.id, None, "save", None, params.model_dump(), result.model_dump())
    return SiteCreateResponse(site=site_response(site), root_option=option_response(option))


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


@router.get("/{site_id}/options")
async def list_options(site_id: UUID, conn: AsyncConnection = Depends(get_connection)) -> list[OptionResponse]:
    if await repository.get_site(conn, site_id) is None:
        raise HTTPException(status_code=404, detail="Site not found")
    records = await repository.list_options(conn, site_id)
    return [option_response(record) for record in records]


@router.post("/{site_id}/options", status_code=201)
async def create_option(
    site_id: UUID, request: OptionCreateRequest, conn: AsyncConnection = Depends(get_connection)
) -> OptionResponse:
    site = await repository.get_site(conn, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    parent = await repository.get_option(conn, request.parent_id)
    if parent is None or parent.site_id != site_id:
        raise HTTPException(status_code=404, detail="Parent option not found")
    params, result = run_massing(site_polygon(site), request.params)
    record = await repository.create_option(
        conn, site_id, request.parent_id, request.kind, request.name, params.model_dump(), result.model_dump()
    )
    return option_response(record)
