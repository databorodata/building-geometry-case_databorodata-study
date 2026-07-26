"""Алгоритм высоты: раскладка общей высоты здания по этажам.

Весь модуль считает в целых дециметрах (23…46 вместо 2.3…4.6): целые числа
складываются и делятся точно, float-хвосты вида 16.400000000000002 исключены
по построению. В метры конвертируем только на выходе.
"""

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
    """Прижимает высоту этажа к сетке 0.1 м и жёсткому диапазону [2.3; 4.6]."""
    height_dm = round(height_m * 10)
    height_dm = max(_FLOOR_MIN_DM, min(_FLOOR_MAX_DM, height_dm))
    return height_dm / 10


def pick_floor_count(total_dm: int, current_count: int) -> int:
    """Выбирает число этажей под общую высоту (в дециметрах).

    Кандидаты — все допустимые этажности 1..8. Победитель — минимум по тройному
    ключу: штраф за выход средней высоты из комфорта [2.8; 3.6] → близость к
    текущему числу этажей (гистерезис: ползунок не «дребезжит» этажами) →
    близость средней высоты к идеалу 3.0.
    """
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
    """Раскладывает высоту на count этажей: деление с остатком, лишние дециметры — нижним этажам.

    Разница между любыми двумя этажами не больше 0.1 м, сумма равна цели точно.
    """
    base, extra = divmod(total_dm, count)
    heights_dm = [base + 1] * extra + [base] * (count - extra)
    return [height / 10 for height in heights_dm]


def distribute_height(total_m: float, current_count: int) -> list[float]:
    """Общая высота здания → список высот этажей (ползунок «Общая высота»).

    Клэмп высоты в [2.3; 24] → выбор числа этажей → раскладка. По построению
    каждый этаж попадает в [2.3; 4.6].
    """
    total_dm = round(total_m * 10)
    total_dm = max(_FLOOR_MIN_DM, min(_MAX_TOTAL_DM, total_dm))
    count = pick_floor_count(total_dm, current_count)
    return spread_floors(total_dm, count)
