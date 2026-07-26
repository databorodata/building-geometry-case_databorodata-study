import pytest

from app.geometry.massing import BuildingParams, FloorParams, MassingParams, compute_massing


def test_default_rectangle(rectangle_site):
    params, result = compute_massing(rectangle_site, None)
    assert result.status == "ok"
    assert params.setback_m == 3.0
    assert result.metrics.building_count == 1
    building = result.buildings[0]
    assert building.contour_area_m2 == pytest.approx(646.0)
    assert building.floor_count == 5
    assert building.height_m == pytest.approx(16.4)
    assert result.metrics.coverage == pytest.approx(0.646)
    assert result.metrics.gfa_m2 == pytest.approx(5 * 646.0, rel=0.01)


def test_default_notched_splits_into_two_buildings(notched_site):
    params = MassingParams(setback_m=4.0)
    params, result = compute_massing(notched_site, params)
    assert result.status == "ok"
    assert result.metrics.building_count == 2
    assert len(params.buildings) == 2
    for building in result.buildings:
        assert building.floor_count >= 1


def test_default_setback_stays_away_from_collapse():
    small_square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    params, result = compute_massing(small_square, None)
    assert result.status == "ok"
    assert result.metrics.building_count == 1
    assert params.setback_m <= result.max_setback_m / 2


def test_floor_area_ratio_can_go_to_half(rectangle_site):
    floors = [FloorParams(height_m=3.0), FloorParams(height_m=3.0, area_ratio=0.5)]
    params = MassingParams(setback_m=3.0, buildings=[BuildingParams(floors=floors)])
    _, result = compute_massing(rectangle_site, params)
    building = result.buildings[0]
    assert building.floors[1].area_m2 == pytest.approx(0.5 * building.contour_area_m2, rel=0.03)


def test_setback_clamped_to_dynamic_max(rectangle_site):
    params = MassingParams(setback_m=50.0)
    params, result = compute_massing(rectangle_site, params)
    assert result.status == "ok"
    assert params.setback_m == pytest.approx(result.max_setback_m)
    assert result.metrics.building_count == 1


def test_setback_change_rebuilds_buildings(notched_site):
    params, _ = compute_massing(notched_site, MassingParams(setback_m=2.0))
    assert len(params.buildings) == 1
    params = params.model_copy(update={"setback_m": 4.0})
    params, result = compute_massing(notched_site, params)
    assert len(params.buildings) == 2
    assert result.metrics.building_count == 2


def test_contour_area_slider(rectangle_site):
    base_params, _ = compute_massing(rectangle_site, None)
    building = base_params.buildings[0].model_copy(update={"contour_area_m2": 400.0})
    params = base_params.model_copy(update={"buildings": [building]})
    _, result = compute_massing(rectangle_site, params)
    assert result.buildings[0].contour_area_m2 == pytest.approx(400.0, rel=0.02)


def test_floor_area_ratio_makes_terrace(rectangle_site):
    floors = [FloorParams(height_m=3.0), FloorParams(height_m=3.0, area_ratio=0.8)]
    params = MassingParams(setback_m=3.0, buildings=[BuildingParams(floors=floors)])
    _, result = compute_massing(rectangle_site, params)
    building = result.buildings[0]
    assert building.floors[1].area_m2 == pytest.approx(0.8 * building.contour_area_m2, rel=0.02)
    assert building.floors[1].level_m == pytest.approx(3.0)


def test_floor_height_out_of_range_is_clamped(rectangle_site):
    floors = [FloorParams(height_m=10.0)]
    params = MassingParams(setback_m=3.0, buildings=[BuildingParams(floors=floors)])
    _, result = compute_massing(rectangle_site, params)
    assert result.buildings[0].floors[0].height_m == 4.6


def test_total_height_edit_redistributes_floors(rectangle_site):
    base_params, _ = compute_massing(rectangle_site, None)
    building = base_params.buildings[0].model_copy(update={"total_height_m": 12.0})
    params = base_params.model_copy(update={"buildings": [building]})
    params, result = compute_massing(rectangle_site, params)
    assert result.buildings[0].floor_count == 4
    assert result.buildings[0].height_m == pytest.approx(12.0)
    assert params.buildings[0].total_height_m is None
    assert [floor.height_m for floor in params.buildings[0].floors] == [3.0, 3.0, 3.0, 3.0]


def test_island_area_reported(rectangle_site):
    _, result = compute_massing(rectangle_site, None)
    assert result.buildings[0].island_area_m2 == pytest.approx(646.0)


def test_total_height_edit_adds_floors(rectangle_site):
    base_params, _ = compute_massing(rectangle_site, None)
    building = base_params.buildings[0].model_copy(update={"total_height_m": 20.0})
    params = base_params.model_copy(update={"buildings": [building]})
    _, result = compute_massing(rectangle_site, params)
    assert result.buildings[0].floor_count == 6
    assert result.buildings[0].height_m == pytest.approx(20.0)


def test_floor_ratio_clamped_up_to_half(rectangle_site):
    floors = [FloorParams(height_m=3.0), FloorParams(height_m=3.0, area_ratio=0.3)]
    params = MassingParams(setback_m=3.0, buildings=[BuildingParams(floors=floors)])
    _, result = compute_massing(rectangle_site, params)
    building = result.buildings[0]
    assert building.floors[1].area_m2 == pytest.approx(0.5 * building.contour_area_m2, rel=0.03)


def test_floor_stack_capped_at_24m(rectangle_site):
    floors = [FloorParams(height_m=4.0) for _ in range(8)]
    params = MassingParams(setback_m=3.0, buildings=[BuildingParams(floors=floors)])
    _, result = compute_massing(rectangle_site, params)
    assert result.buildings[0].floor_count == 6
    assert result.buildings[0].height_m == pytest.approx(24.0)


def test_default_l_shaped(l_shaped_site):
    _, result = compute_massing(l_shaped_site, None)
    assert result.status == "ok"
    assert result.metrics.building_count == 1
    building = result.buildings[0]
    assert 1 <= building.floor_count <= 8
    assert building.gfa_m2 > 0
    assert building.contour_area_m2 < result.metrics.site_area_m2


def test_default_notched_splits_at_threshold(notched_site):
    params, result = compute_massing(notched_site, None)
    assert params.setback_m == pytest.approx(3.0)
    assert result.metrics.building_count == 2


def test_empty_floors_rebuilt_with_default(rectangle_site):
    params = MassingParams(setback_m=3.0, buildings=[BuildingParams(floors=[])])
    params, result = compute_massing(rectangle_site, params)
    assert result.buildings[0].floor_count == 5
    assert len(params.buildings[0].floors) == 5


def test_gfa_target_check_accounts_for_movable_setback(rectangle_site):
    params = MassingParams(setback_m=3.0, gfa_target_m2=6000.0)
    params, result = compute_massing(rectangle_site, params)
    assert result.gfa_check is not None
    assert result.gfa_check.reachable is True
    assert result.gfa_check.max_possible_m2 == pytest.approx(8 * 1000.0)
    assert 0 < result.gfa_check.min_possible_m2 < 30
    params = params.model_copy(update={"gfa_target_m2": 9000.0})
    _, result = compute_massing(rectangle_site, params)
    assert result.gfa_check is not None
    assert result.gfa_check.reachable is False


def test_gfa_target_check_with_locked_building(rectangle_site):
    base_params, _ = compute_massing(rectangle_site, None)
    locked = base_params.buildings[0].model_copy(update={"locked": True})
    params = base_params.model_copy(update={"buildings": [locked], "gfa_target_m2": 6000.0})
    _, result = compute_massing(rectangle_site, params)
    assert result.gfa_check is not None
    assert result.gfa_check.max_possible_m2 == pytest.approx(8 * 646.0, rel=0.01)
    assert result.gfa_check.reachable is False


def test_default_tiny_site_single_floor():
    params, result = compute_massing([(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)], None)
    assert params.setback_m == 0.0
    assert result.metrics.building_count == 1
    assert result.buildings[0].floor_count == 1
    assert result.buildings[0].height_m == pytest.approx(2.8)


def test_default_huge_site_clamped_to_limits():
    _, result = compute_massing([(0.0, 0.0), (200.0, 0.0), (200.0, 200.0), (0.0, 200.0)], None)
    assert result.buildings[0].floor_count == 8
    assert result.buildings[0].height_m == pytest.approx(24.0)


def test_default_thin_site():
    params, result = compute_massing([(0.0, 0.0), (100.0, 0.0), (100.0, 8.0), (0.0, 8.0)], None)
    assert params.setback_m == pytest.approx(1.9)
    assert result.metrics.building_count == 1
    assert result.buildings[0].floor_count == 8


def test_height_edit_preserves_floor_flags(rectangle_site):
    base_params, _ = compute_massing(rectangle_site, None)
    building = base_params.buildings[0]
    floors = list(building.floors)
    floors[1] = floors[1].model_copy(update={"area_ratio": 0.7, "contour_locked": True})
    building = building.model_copy(update={"floors": floors, "total_height_m": 12.0})
    params = base_params.model_copy(update={"buildings": [building]})
    params, result = compute_massing(rectangle_site, params)
    assert result.buildings[0].floor_count == 4
    assert params.buildings[0].floors[1].area_ratio == 0.7
    assert params.buildings[0].floors[1].contour_locked is True


def test_height_edit_clamps_out_of_range(rectangle_site):
    base_params, _ = compute_massing(rectangle_site, None)
    building = base_params.buildings[0].model_copy(update={"total_height_m": 100.0})
    _, result = compute_massing(rectangle_site, base_params.model_copy(update={"buildings": [building]}))
    assert result.buildings[0].height_m == pytest.approx(24.0)
    building = base_params.buildings[0].model_copy(update={"total_height_m": 1.0})
    _, result = compute_massing(rectangle_site, base_params.model_copy(update={"buildings": [building]}))
    assert result.buildings[0].floor_count == 1
    assert result.buildings[0].height_m == pytest.approx(2.3)


def test_floors_truncated_to_eight(rectangle_site):
    floors = [FloorParams(height_m=2.3) for _ in range(10)]
    params = MassingParams(setback_m=3.0, buildings=[BuildingParams(floors=floors)])
    _, result = compute_massing(rectangle_site, params)
    assert result.buildings[0].floor_count == 8
    assert result.buildings[0].height_m == pytest.approx(18.4)


def test_floor_levels_cumulative(rectangle_site):
    floors = [FloorParams(height_m=2.5), FloorParams(height_m=3.0), FloorParams(height_m=4.0)]
    params = MassingParams(setback_m=3.0, buildings=[BuildingParams(floors=floors)])
    _, result = compute_massing(rectangle_site, params)
    levels = [floor.level_m for floor in result.buildings[0].floors]
    assert levels == [0.0, 2.5, 5.5]
    assert result.buildings[0].height_m == pytest.approx(9.5)


def test_negative_setback_clamped_to_zero(rectangle_site):
    params, result = compute_massing(rectangle_site, MassingParams(setback_m=-5.0))
    assert params.setback_m == 0.0
    assert result.metrics.buildable_area_m2 == pytest.approx(1000.0)


def test_mismatch_rebuild_drops_custom_floors(notched_site):
    custom = BuildingParams(floors=[FloorParams(height_m=4.6)])
    params = MassingParams(setback_m=4.0, buildings=[custom])
    params, result = compute_massing(notched_site, params)
    assert result.metrics.building_count == 2
    for building in params.buildings:
        assert [floor.height_m for floor in building.floors] == [3.7, 3.7]


def test_zero_gfa_target_gives_no_check(rectangle_site):
    params = MassingParams(setback_m=3.0, gfa_target_m2=0.0)
    _, result = compute_massing(rectangle_site, params)
    assert result.gfa_check is None


def test_double_notch_makes_three_buildings():
    comb = [
        (0, 0),
        (70, 0),
        (70, 20),
        (50, 20),
        (50, 6),
        (45, 6),
        (45, 20),
        (25, 20),
        (25, 6),
        (20, 6),
        (20, 20),
        (0, 20),
    ]
    points = [(float(x), float(y)) for x, y in comb]
    params, result = compute_massing(points, MassingParams(setback_m=4.0))
    assert result.metrics.building_count == 3
    for building in result.buildings:
        assert building.island_area_m2 == pytest.approx(144.0, rel=0.02)
        assert building.floor_count >= 1


def test_metrics_invariants_on_shape_zoo(rectangle_site, l_shaped_site, notched_site):
    comb = [
        (0.0, 0.0),
        (70.0, 0.0),
        (70.0, 20.0),
        (50.0, 20.0),
        (50.0, 6.0),
        (45.0, 6.0),
        (45.0, 20.0),
        (25.0, 20.0),
        (25.0, 6.0),
        (20.0, 6.0),
        (20.0, 20.0),
        (0.0, 20.0),
    ]
    star = [(0.0, 0.0), (15.0, 5.0), (30.0, 0.0), (25.0, 15.0), (30.0, 30.0), (15.0, 25.0), (0.0, 30.0), (5.0, 15.0)]
    pentagon = [(0.0, 0.0), (30.0, 0.0), (40.0, 20.0), (15.0, 35.0), (-10.0, 20.0)]
    tiny = [(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)]
    for points in (rectangle_site, l_shaped_site, notched_site, comb, star, pentagon, tiny):
        params, result = compute_massing(points, None)
        metrics = result.metrics
        assert result.status == "ok"
        assert metrics.coverage <= 1.001
        assert metrics.far == pytest.approx(metrics.gfa_m2 / metrics.site_area_m2, abs=0.01)
        assert metrics.building_count == len(params.buildings) == len(result.buildings)
        assert metrics.footprint_area_m2 <= metrics.buildable_area_m2 + 0.5
        assert metrics.buildable_area_m2 <= metrics.site_area_m2 + 0.5
        assert result.max_setback_m >= 0.0
        total_volume = 0.0
        for building in result.buildings:
            assert 1 <= building.floor_count <= 8
            assert building.height_m <= 24.001
            level = 0.0
            for floor in building.floors:
                assert 2.3 <= floor.height_m <= 4.6
                assert floor.level_m == pytest.approx(level, abs=0.01)
                level += floor.height_m
            assert building.volume_m3 == pytest.approx(sum(f.volume_m3 for f in building.floors), rel=0.01)
            total_volume += building.volume_m3
        assert metrics.volume_m3 == pytest.approx(total_volume, rel=0.01)
