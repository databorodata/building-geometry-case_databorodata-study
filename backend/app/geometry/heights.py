import math

from app.geometry.limits import (
    COMFORT_HEIGHT_MAX_M,
    COMFORT_HEIGHT_MIN_M,
    DEFAULT_FLOOR_HEIGHT_M,
    FLOOR_HEIGHT_MAX_M,
    FLOOR_HEIGHT_MIN_M,
    MAX_BUILDING_HEIGHT_M,
    MAX_FLOORS,
)

_FLOOR_MIN_DM = round(FLOOR_HEIGHT_MIN_M * 10)
_FLOOR_MAX_DM = round(FLOOR_HEIGHT_MAX_M * 10)
_COMFORT_MIN_DM = round(COMFORT_HEIGHT_MIN_M * 10)
_COMFORT_MAX_DM = round(COMFORT_HEIGHT_MAX_M * 10)
_DEFAULT_DM = round(DEFAULT_FLOOR_HEIGHT_M * 10)
_MAX_TOTAL_DM = round(MAX_BUILDING_HEIGHT_M * 10)


def clamp_floor_height(height_m: float) -> float:
    height_dm = round(height_m * 10)
    height_dm = max(_FLOOR_MIN_DM, min(_FLOOR_MAX_DM, height_dm))
    return height_dm / 10


def pick_floor_count(total_dm: int, current_count: int) -> int:
    count_min = max(1, math.ceil(total_dm / _FLOOR_MAX_DM))
    count_max = min(MAX_FLOORS, total_dm // _FLOOR_MIN_DM)
    if count_max < count_min:
        count_max = count_min
    best_count = count_min
    best_key: tuple[float, int, float] | None = None
    for count in range(count_min, count_max + 1):
        height = total_dm / count
        penalty = max(0.0, _COMFORT_MIN_DM - height) + max(0.0, height - _COMFORT_MAX_DM)
        key = (penalty, abs(count - current_count), abs(height - _DEFAULT_DM))
        if best_key is None or key < best_key:
            best_key = key
            best_count = count
    return best_count


def spread_floors(total_dm: int, count: int) -> list[float]:
    base, extra = divmod(total_dm, count)
    heights_dm = [base + 1] * extra + [base] * (count - extra)
    return [height / 10 for height in heights_dm]


def distribute_height(total_m: float, current_count: int) -> list[float]:
    total_dm = round(total_m * 10)
    total_dm = max(_FLOOR_MIN_DM, min(_MAX_TOTAL_DM, total_dm))
    count = pick_floor_count(total_dm, current_count)
    return spread_floors(total_dm, count)
