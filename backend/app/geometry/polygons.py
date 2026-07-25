import math

from shapely.geometry import Polygon

from app.geometry.limits import MIN_BUILDING_AREA_M2

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
