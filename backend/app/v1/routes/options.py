from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import AsyncConnection
from pydantic import BaseModel

from app import repository
from app.db import get_connection
from app.geometry.massing import EnsembleMetrics
from app.v1.routes.sites import OptionResponse, option_response

router = APIRouter(prefix="/options", tags=["options"])


class CompareSide(BaseModel):
    id: UUID
    name: str | None
    metrics: EnsembleMetrics


class CompareResponse(BaseModel):
    left: CompareSide
    right: CompareSide
    delta: dict[str, float]


def metrics_delta(left: EnsembleMetrics, right: EnsembleMetrics) -> dict[str, float]:
    return {
        "footprint_area_m2": round(right.footprint_area_m2 - left.footprint_area_m2, 1),
        "gfa_m2": round(right.gfa_m2 - left.gfa_m2, 1),
        "volume_m3": round(right.volume_m3 - left.volume_m3, 1),
        "coverage": round(right.coverage - left.coverage, 3),
        "far": round(right.far - left.far, 3),
        "max_height_m": round(right.max_height_m - left.max_height_m, 1),
        "building_count": right.building_count - left.building_count,
    }


async def load_option(conn: AsyncConnection, option_id: UUID) -> OptionResponse:
    record = await repository.get_option(conn, option_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Option not found")
    return option_response(record)


@router.get("/{option_id}")
async def get_option(option_id: UUID, conn: AsyncConnection = Depends(get_connection)) -> OptionResponse:
    return await load_option(conn, option_id)


@router.get("/{option_id}/compare/{other_id}")
async def compare_options(
    option_id: UUID, other_id: UUID, conn: AsyncConnection = Depends(get_connection)
) -> CompareResponse:
    left = await load_option(conn, option_id)
    right = await load_option(conn, other_id)
    if left.site_id != right.site_id:
        raise HTTPException(status_code=422, detail="Options belong to different sites")
    return CompareResponse(
        left=CompareSide(id=left.id, name=left.name, metrics=left.result.metrics),
        right=CompareSide(id=right.id, name=right.name, metrics=right.result.metrics),
        delta=metrics_delta(left.result.metrics, right.result.metrics),
    )
