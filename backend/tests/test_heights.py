import pytest

from app.geometry import heights


def test_even_split_keeps_count():
    assert heights.distribute_height(9.0, 3) == [3.0, 3.0, 3.0]


def test_remainder_goes_to_bottom_floors():
    floors = heights.distribute_height(10.0, 3)
    assert floors == [3.4, 3.3, 3.3]
    assert sum(floors) == pytest.approx(10.0)


def test_adds_floor_to_stay_in_comfort():
    floors = heights.distribute_height(12.0, 3)
    assert len(floors) == 4
    assert floors == [3.0, 3.0, 3.0, 3.0]


def test_tall_single_floor_splits_in_two():
    floors = heights.distribute_height(4.8, 1)
    assert floors == [2.4, 2.4]


def test_single_floor_boundary():
    assert heights.distribute_height(4.5, 1) == [4.5]
    assert heights.distribute_height(4.6, 1) == [2.3, 2.3]


def test_hysteresis_keeps_current_count():
    assert len(heights.distribute_height(14.4, 4)) == 4
    assert len(heights.distribute_height(14.4, 5)) == 5


def test_no_dead_zone_above_max_single_floor():
    floors = heights.distribute_height(4.7, 1)
    assert len(floors) == 2
    assert sum(floors) == pytest.approx(4.7)


def test_clamps_to_building_limits():
    floors = heights.distribute_height(30.0, 8)
    assert len(floors) == 8
    assert sum(floors) == pytest.approx(24.0)
    assert heights.distribute_height(2.0, 1) == [2.3]


def test_all_floors_within_hard_range():
    for total_dm in range(23, 241):
        floors = heights.distribute_height(total_dm / 10, 3)
        for height in floors:
            assert 2.3 <= height <= 4.6
        assert sum(floors) == pytest.approx(total_dm / 10)


def test_clamp_floor_height():
    assert heights.clamp_floor_height(1.0) == 2.3
    assert heights.clamp_floor_height(5.0) == 4.6
    assert heights.clamp_floor_height(3.14) == 3.1


def test_max_height_from_single_floor():
    floors = heights.distribute_height(24.0, 1)
    assert len(floors) == 7
    assert sum(floors) == pytest.approx(24.0)


def test_max_height_keeps_eight_floors():
    assert heights.distribute_height(24.0, 8) == [3.0] * 8


def test_comfort_switch_boundary():
    assert len(heights.distribute_height(10.8, 3)) == 3
    assert len(heights.distribute_height(11.2, 3)) == 4


def test_weird_current_count_does_not_crash():
    assert heights.distribute_height(9.0, 0) == [3.0, 3.0, 3.0]
    assert heights.distribute_height(9.0, 99) == [3.0, 3.0, 3.0]


def test_spread_floors_direct():
    floors = heights.spread_floors(233, 7)
    assert floors == [3.4, 3.4, 3.3, 3.3, 3.3, 3.3, 3.3]
    assert sum(floors) == pytest.approx(23.3)


def test_below_minimum_clamps():
    assert heights.distribute_height(-5.0, 1) == [2.3]
    assert heights.distribute_height(0.0, 3) == [2.3]


def test_pick_floor_count_bounds():
    assert heights.pick_floor_count(23, 1) == 1
    assert 6 <= heights.pick_floor_count(240, 8) <= 8
