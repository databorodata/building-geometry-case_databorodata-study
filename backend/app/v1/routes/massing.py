"""Расчёт массинга без сохранения — рабочая лошадка живого редактора."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.geometry.massing import MassingParams, MassingResult, compute_massing
from app.geometry.polygons import Point, SiteError

router = APIRouter(prefix="/massing", tags=["massing"])


class PreviewRequest(BaseModel):
    polygon: list[Point]
    params: MassingParams | None = None


class PreviewResponse(BaseModel):
    params: MassingParams
    result: MassingResult


def run_massing(polygon: list[Point], params: MassingParams | None) -> tuple[MassingParams, MassingResult]:
    """Единственное место перевода доменной ошибки в HTTP: SiteError → 422 {code, message}.

    Импортируется и роутами сохранения — обработка ошибок не копипастится.
    """
    try:
        return compute_massing(polygon, params)
    except SiteError as error:
        raise HTTPException(status_code=422, detail={"code": error.code, "message": error.message}) from error


@router.post("/preview")
async def preview(request: PreviewRequest) -> PreviewResponse:
    """Stateless-расчёт без БД: каждое движение ползунка (после debounce) бьёт сюда.

    params = null → сервер сам строит φ-дефолт (первая карточка).
    """
    params, result = run_massing(request.polygon, request.params)
    return PreviewResponse(params=params, result=result)
