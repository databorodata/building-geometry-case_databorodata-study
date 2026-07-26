import math

from pydantic import BaseModel
from shapely.geometry import Polygon

from app.geometry import heights, polygons
from app.geometry.limits import (
    DEFAULT_FLOOR_HEIGHT_M,
    DEFAULT_SETBACK_M,
    GOLDEN_RATIO,
    MAX_BUILDING_HEIGHT_M,
    MAX_FLOORS,
    MIN_FLOOR_AREA_RATIO,
)
from app.geometry.polygons import Point


class FloorParams(BaseModel):
    height_m: float = DEFAULT_FLOOR_HEIGHT_M
    area_ratio: float = 1.0
    height_locked: bool = False
    contour_locked: bool = False


class BuildingParams(BaseModel):
    contour_area_m2: float | None = None
    total_height_m: float | None = None
    locked: bool = False
    floors: list[FloorParams]


class MassingParams(BaseModel):
    setback_m: float = DEFAULT_SETBACK_M
    gfa_target_m2: float | None = None
    buildings: list[BuildingParams] = []


class FloorResult(BaseModel):
    outline: list[Point]
    level_m: float
    height_m: float
    area_m2: float
    volume_m3: float


class BuildingResult(BaseModel):
    contour: list[Point]
    contour_area_m2: float
    island_area_m2: float
    min_contour_area_m2: float
    floor_count: int
    height_m: float
    gfa_m2: float
    volume_m3: float
    floors: list[FloorResult]


class EnsembleMetrics(BaseModel):
    site_area_m2: float
    buildable_area_m2: float
    footprint_area_m2: float
    gfa_m2: float
    volume_m3: float
    coverage: float
    far: float
    max_height_m: float
    building_count: int


class GfaCheck(BaseModel):
    target_m2: float
    min_possible_m2: float
    max_possible_m2: float
    reachable: bool


class MassingResult(BaseModel):
    status: str
    reason: str | None = None
    max_setback_m: float
    site_outline: list[Point]
    metrics: EnsembleMetrics
    buildings: list[BuildingResult]
    gfa_check: GfaCheck | None = None


def default_floor_stack(island: Polygon) -> list[FloorParams]:
    min_x, min_y, max_x, max_y = island.bounds
    facade_m = ((max_x - min_x) + (max_y - min_y)) / 2
    ideal_height_m = facade_m / GOLDEN_RATIO
    start_count = max(1, round(ideal_height_m / DEFAULT_FLOOR_HEIGHT_M))
    floor_heights = heights.distribute_height(ideal_height_m, start_count)
    return [FloorParams(height_m=height) for height in floor_heights]


def default_params(site: Polygon) -> MassingParams:
    limit = polygons.max_setback(site)
    half_limit = limit / 2
    safe_limit = math.floor(half_limit * 10) / 10
    setback = min(DEFAULT_SETBACK_M, safe_limit)
    islands = polygons.inset_islands(site, setback)
    buildings = [BuildingParams(floors=default_floor_stack(island)) for island in islands]
    return MassingParams(setback_m=setback, buildings=buildings)


def apply_height_edit(params: BuildingParams) -> BuildingParams:
    if params.total_height_m is None:
        return params
    new_heights = heights.distribute_height(params.total_height_m, max(1, len(params.floors)))
    floors: list[FloorParams] = []
    for index, height in enumerate(new_heights):
        if index < len(params.floors):
            floors.append(params.floors[index].model_copy(update={"height_m": height}))
        else:
            floors.append(FloorParams(height_m=height))
    return params.model_copy(update={"floors": floors, "total_height_m": None})


def clamped_ratios(floors: list[FloorParams]) -> list[float]:
    return [max(MIN_FLOOR_AREA_RATIO, min(1.0, floor.area_ratio)) for floor in floors]


def clamped_contour_area(params: BuildingParams, island_area: float, min_area: float) -> float:
    if params.contour_area_m2 is None:
        return island_area
    return max(min(params.contour_area_m2, island_area), min_area)


def build_building(island: Polygon, params: BuildingParams) -> BuildingResult:
    min_area = polygons.min_contour_area(island)
    target_area = clamped_contour_area(params, island.area, min_area)
    contour = polygons.erode_to_area(island, target_area)
    floors: list[FloorResult] = []
    level_dm = 0
    gfa = 0.0
    volume = 0.0
    stack = params.floors[:MAX_FLOORS]
    for floor, ratio in zip(stack, clamped_ratios(stack)):
        height_m = heights.clamp_floor_height(floor.height_m)
        height_dm = round(height_m * 10)
        if (level_dm + height_dm) / 10 > MAX_BUILDING_HEIGHT_M:
            break
        if ratio < 1.0:
            outline_polygon = polygons.erode_to_area(contour, contour.area * ratio)
        else:
            outline_polygon = contour
        area = outline_polygon.area
        floors.append(
            FloorResult(
                outline=polygons.polygon_outline(outline_polygon),
                level_m=level_dm / 10,
                height_m=height_m,
                area_m2=round(area, 1),
                volume_m3=round(area * height_m, 1),
            )
        )
        level_dm += height_dm
        gfa += area
        volume += area * height_m
    return BuildingResult(
        contour=polygons.polygon_outline(contour),
        contour_area_m2=round(contour.area, 1),
        island_area_m2=round(island.area, 1),
        min_contour_area_m2=round(min_area, 1),
        floor_count=len(floors),
        height_m=level_dm / 10,
        gfa_m2=round(gfa, 1),
        volume_m3=round(volume, 1),
        floors=floors,
    )


def rollup_metrics(site: Polygon, islands: list[Polygon], buildings: list[BuildingResult]) -> EnsembleMetrics:
    site_area = site.area
    buildable = sum(island.area for island in islands)
    footprint = sum(building.contour_area_m2 for building in buildings)
    gfa = sum(building.gfa_m2 for building in buildings)
    volume = sum(building.volume_m3 for building in buildings)
    max_height = max((building.height_m for building in buildings), default=0.0)
    return EnsembleMetrics(
        site_area_m2=round(site_area, 1),
        buildable_area_m2=round(buildable, 1),
        footprint_area_m2=round(footprint, 1),
        gfa_m2=round(gfa, 1),
        volume_m3=round(volume, 1),
        coverage=round(footprint / site_area, 3),
        far=round(gfa / site_area, 3),
        max_height_m=max_height,
        building_count=len(buildings),
    )


def compute_massing(points: list[Point], params: MassingParams | None) -> tuple[MassingParams, MassingResult]:
    site = polygons.validate_site(points)
    if params is None:
        params = default_params(site)
    setback_limit = polygons.max_setback(site)
    setback = max(0.0, min(params.setback_m, setback_limit))
    islands = polygons.inset_islands(site, setback)
    site_outline = polygons.polygon_outline(site)
    if not islands:
        empty_metrics = EnsembleMetrics(
            site_area_m2=round(site.area, 1),
            buildable_area_m2=0.0,
            footprint_area_m2=0.0,
            gfa_m2=0.0,
            volume_m3=0.0,
            coverage=0.0,
            far=0.0,
            max_height_m=0.0,
            building_count=0,
        )
        result = MassingResult(
            status="empty",
            reason="setback_collapses_site",
            max_setback_m=setback_limit,
            site_outline=site_outline,
            metrics=empty_metrics,
            buildings=[],
        )
        return params.model_copy(update={"setback_m": setback}), result
    building_params = params.buildings
    if len(building_params) != len(islands):
        building_params = [BuildingParams(floors=default_floor_stack(island)) for island in islands]
    refreshed: list[BuildingParams] = []
    for island, item in zip(islands, building_params):
        if not item.floors:
            item = item.model_copy(update={"floors": default_floor_stack(island)})
        refreshed.append(item)
    building_params = [apply_height_edit(item) for item in refreshed]
    params = params.model_copy(update={"setback_m": setback, "buildings": building_params})
    buildings = [build_building(island, item) for island, item in zip(islands, building_params)]
    metrics = rollup_metrics(site, islands, buildings)
    gfa_check = None
    if params.gfa_target_m2 is not None and params.gfa_target_m2 > 0:
        if any(item.locked for item in building_params):
            bound_islands = islands
            max_possible = sum(island.area for island in islands) * MAX_FLOORS
        else:
            bound_islands = polygons.inset_islands(site, setback_limit)
            max_possible = site.area * MAX_FLOORS
        min_possible = sum(polygons.min_contour_area(island) for island in bound_islands) * MIN_FLOOR_AREA_RATIO
        gfa_check = GfaCheck(
            target_m2=params.gfa_target_m2,
            min_possible_m2=round(min_possible, 1),
            max_possible_m2=round(max_possible, 1),
            reachable=min_possible <= params.gfa_target_m2 <= max_possible,
        )
    result = MassingResult(
        status="ok",
        max_setback_m=setback_limit,
        site_outline=site_outline,
        metrics=metrics,
        buildings=buildings,
        gfa_check=gfa_check,
    )
    return params, result
