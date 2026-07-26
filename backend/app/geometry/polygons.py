import math

from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from app.geometry.limits import MIN_BUILDING_AREA_M2, SETBACK_STEP_M

Point = tuple[float, float]


class SiteError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def validate_site(points: list[Point]) -> Polygon:
    cleaned = [(float(x), float(y)) for x, y in points]
    for x, y in cleaned:
        if not (math.isfinite(x) and math.isfinite(y)):
            raise SiteError("bad_coordinates", "Site coordinates must be finite numbers")
    if len(cleaned) > 1 and cleaned[0] == cleaned[-1]:
        cleaned = cleaned[:-1]
    if len(set(cleaned)) < 3:
        raise SiteError("too_few_points", "Site polygon needs at least 3 distinct points")
    polygon = Polygon(cleaned)
    if not polygon.is_valid:
        raise SiteError("invalid_polygon", "Site polygon must be simple (no self-intersections)")
    if polygon.area < MIN_BUILDING_AREA_M2:
        raise SiteError("site_too_small", f"Site area must be at least {MIN_BUILDING_AREA_M2} m2")
    return polygon


def polygon_parts(geometry: BaseGeometry) -> list[Polygon]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return [part for part in geometry.geoms if not part.is_empty]
    return []


def polygon_outline(polygon: Polygon) -> list[Point]:
    coords = list(polygon.exterior.coords)[:-1]
    return [(round(x, 2), round(y, 2)) for x, y in coords]


def inset_islands(site: Polygon, depth: float) -> list[Polygon]:
    if depth <= 0:
        shrunk: BaseGeometry = site
    else:
        shrunk = site.buffer(-depth, join_style="mitre")
    islands = [part for part in polygon_parts(shrunk) if part.area >= MIN_BUILDING_AREA_M2]
    islands.sort(key=lambda part: (round(part.centroid.x, 1), round(part.centroid.y, 1)))
    return islands


def max_setback(site: Polygon) -> float:
    min_x, min_y, max_x, max_y = site.bounds
    low = 0.0
    high = max(max_x - min_x, max_y - min_y)
    for _ in range(40):
        middle = (low + high) / 2
        if inset_islands(site, middle):
            low = middle
        else:
            high = middle
    return math.floor(low / SETBACK_STEP_M) * SETBACK_STEP_M


def erode_to_area(polygon: Polygon, target_area: float) -> Polygon:
    if target_area >= polygon.area:
        return polygon
    min_x, min_y, max_x, max_y = polygon.bounds
    low = 0.0
    high = max(max_x - min_x, max_y - min_y)
    for _ in range(40):
        middle = (low + high) / 2
        parts = polygon_parts(polygon.buffer(-middle, join_style="mitre"))
        area = sum(part.area for part in parts)
        if area > target_area:
            low = middle
        else:
            high = middle
    parts = polygon_parts(polygon.buffer(-low, join_style="mitre"))
    if not parts:
        return polygon
    return max(parts, key=lambda part: part.area)


def min_contour_area(contour: Polygon) -> float:
    area = contour.area
    depth = SETBACK_STEP_M
    while True:
        parts = [
            part
            for part in polygon_parts(contour.buffer(-depth, join_style="mitre"))
            if part.area >= MIN_BUILDING_AREA_M2
        ]
        if len(parts) != 1:
            return area
        area = parts[0].area
        depth += SETBACK_STEP_M
