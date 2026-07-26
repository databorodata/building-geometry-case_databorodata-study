import math

from pydantic import BaseModel
from shapely.geometry import Polygon

from app.geometry import heights, polygons
from app.geometry.limits import (
    DEFAULT_FLOOR_HEIGHT_M,
    DEFAULT_SETBACK_M,
    FLOOR_HEIGHT_MIN_M,
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
    fit_gfa_m2: float | None = None
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


class FitInfo(BaseModel):
    island_area: float
    min_area: float
    gfa: float
    min_gfa: float
    max_gfa: float
    active: bool


def clamped_ratios(floors: list[FloorParams]) -> list[float]:
    return [max(MIN_FLOOR_AREA_RATIO, min(1.0, floor.area_ratio)) for floor in floors]


def clamped_contour_area(params: BuildingParams, island_area: float, min_area: float) -> float:
    if params.contour_area_m2 is None:
        return island_area
    return max(min(params.contour_area_m2, island_area), min_area)


def fit_building_to_gfa(params: BuildingParams, island_area: float, min_area: float, target: float) -> BuildingParams:
    floors = params.floors[:MAX_FLOORS]
    if not floors:
        return params
    contour = clamped_contour_area(params, island_area, min_area)
    ratios = clamped_ratios(floors)
    heights_sum = sum(heights.clamp_floor_height(floor.height_m) for floor in floors)
    current_gfa = contour * sum(ratios)
    can_floors = not any(floor.height_locked for floor in floors)
    can_contour = not any(floor.contour_locked for floor in floors)
    count = len(floors)
    counts = range(1, MAX_FLOORS + 1) if can_floors else range(count, count + 1)
    if contour > 0:
        ideal_count = count + 0.5 * (target - current_gfa) / contour
    else:
        ideal_count = float(count)

    best_key: tuple[float, float, int] | None = None
    best_count = count
    best_contour = contour
    best_gfa = current_gfa
    for candidate in counts:
        if candidate > count:
            added = candidate - count
            if heights_sum + added * FLOOR_HEIGHT_MIN_M > MAX_BUILDING_HEIGHT_M + 1e-9:
                continue
            ratio_sum = sum(ratios) + added
        else:
            ratio_sum = sum(ratios[:candidate])
        if can_contour:
            new_contour = max(min(target / ratio_sum, island_area), min_area)
        else:
            new_contour = contour
        gfa = new_contour * ratio_sum
        key = (round(abs(target - gfa), 3), abs(candidate - ideal_count), abs(candidate - count))
        if best_key is None or key < best_key:
            best_key = key
            best_count = candidate
            best_contour = new_contour
            best_gfa = gfa

    if abs(target - best_gfa) >= abs(target - current_gfa) - 1e-9:
        return params
    new_floors = [floor.model_copy() for floor in floors[:best_count]]
    if best_count > count:
        added = best_count - count
        room = (MAX_BUILDING_HEIGHT_M - heights_sum) / added
        height = min(DEFAULT_FLOOR_HEIGHT_M, math.floor(room * 10) / 10)
        for _ in range(added):
            new_floors.append(FloorParams(height_m=height))
    if best_contour >= island_area - 0.05:
        contour_param = None
    else:
        contour_param = round(best_contour, 1)
    return params.model_copy(update={"floors": new_floors, "contour_area_m2": contour_param, "total_height_m": None})


def apply_gfa_fit(
    building_params: list[BuildingParams], islands: list[Polygon], target_total: float
) -> list[BuildingParams]:
    infos: list[FitInfo] = []
    for item, island in zip(building_params, islands):
        island_area = island.area
        min_area = polygons.min_contour_area(island)
        floors = item.floors[:MAX_FLOORS]
        ratios = clamped_ratios(floors)
        contour = clamped_contour_area(item, island_area, min_area)
        gfa = contour * sum(ratios)
        can_floors = len(floors) > 0 and not any(floor.height_locked for floor in floors)
        can_contour = len(floors) > 0 and not any(floor.contour_locked for floor in floors)
        heights_sum = sum(heights.clamp_floor_height(floor.height_m) for floor in floors)
        if can_floors:
            max_added = int((MAX_BUILDING_HEIGHT_M - heights_sum) / FLOOR_HEIGHT_MIN_M)
            max_count = min(MAX_FLOORS, len(floors) + max_added)
            max_ratio = sum(ratios) + (max_count - len(floors))
            min_ratio = sum(ratios[:1])
        else:
            max_ratio = sum(ratios)
            min_ratio = sum(ratios)
        max_contour = island_area if can_contour else contour
        min_contour_value = min_area if can_contour else contour
        active = not item.locked and len(floors) > 0 and (can_floors or can_contour)
        infos.append(
            FitInfo(
                island_area=island_area,
                min_area=min_area,
                gfa=gfa,
                min_gfa=min_contour_value * min_ratio,
                max_gfa=max_contour * max_ratio,
                active=active,
            )
        )

    active_indexes = [index for index, info in enumerate(infos) if info.active]
    if not active_indexes:
        return building_params
    fixed = sum(info.gfa for info in infos if not info.active)
    remaining = max(target_total - fixed, 0.0)
    active_gfa = sum(infos[index].gfa for index in active_indexes)
    targets: dict[int, float] = {}
    for index in active_indexes:
        if active_gfa > 0:
            share = infos[index].gfa / active_gfa
        else:
            share = 1.0 / len(active_indexes)
        raw = remaining * share
        targets[index] = max(min(raw, infos[index].max_gfa), infos[index].min_gfa)
    unmet = remaining - sum(targets.values())
    if unmet > 0:
        headroom = {index: infos[index].max_gfa - targets[index] for index in active_indexes}
        total_headroom = sum(headroom.values())
        if total_headroom > 0:
            for index in active_indexes:
                targets[index] += unmet * headroom[index] / total_headroom
    elif unmet < 0:
        droproom = {index: targets[index] - infos[index].min_gfa for index in active_indexes}
        total_droproom = sum(droproom.values())
        if total_droproom > 0:
            for index in active_indexes:
                targets[index] += unmet * droproom[index] / total_droproom

    fitted = list(building_params)
    for index in active_indexes:
        fitted[index] = fit_building_to_gfa(
            building_params[index], infos[index].island_area, infos[index].min_area, targets[index]
        )
    return fitted


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
        return params.model_copy(update={"setback_m": setback, "fit_gfa_m2": None}), result
    building_params = params.buildings
    if len(building_params) != len(islands):
        building_params = [BuildingParams(floors=default_floor_stack(island)) for island in islands]
    refreshed: list[BuildingParams] = []
    for island, item in zip(islands, building_params):
        if not item.floors:
            item = item.model_copy(update={"floors": default_floor_stack(island)})
        refreshed.append(item)
    building_params = [apply_height_edit(item) for item in refreshed]
    if params.fit_gfa_m2 is not None and params.fit_gfa_m2 > 0:
        building_params = apply_gfa_fit(building_params, islands, params.fit_gfa_m2)
    params = params.model_copy(update={"setback_m": setback, "buildings": building_params, "fit_gfa_m2": None})
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
