import pytest

from app.geometry import polygons


def test_validate_site_accepts_rectangle(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    assert site.area == pytest.approx(1000.0)


def test_validate_site_rejects_too_few_points():
    with pytest.raises(polygons.SiteError) as error:
        polygons.validate_site([(0.0, 0.0), (10.0, 0.0)])
    assert error.value.code == "too_few_points"


def test_validate_site_rejects_self_intersection():
    bowtie = [(0.0, 0.0), (10.0, 10.0), (10.0, 0.0), (0.0, 10.0)]
    with pytest.raises(polygons.SiteError) as error:
        polygons.validate_site(bowtie)
    assert error.value.code == "invalid_polygon"


def test_validate_site_rejects_too_small():
    with pytest.raises(polygons.SiteError) as error:
        polygons.validate_site([(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)])
    assert error.value.code == "site_too_small"


def test_validate_site_rejects_nan():
    with pytest.raises(polygons.SiteError) as error:
        polygons.validate_site([(0.0, 0.0), (float("nan"), 0.0), (10.0, 10.0)])
    assert error.value.code == "bad_coordinates"


def test_validate_site_drops_closing_point():
    site = polygons.validate_site([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)])
    assert site.area == pytest.approx(100.0)


def test_validate_site_rejects_degenerate():
    with pytest.raises(polygons.SiteError):
        polygons.validate_site([(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)])


def test_inset_rectangle_shrinks_area(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    islands = polygons.inset_islands(site, 3.0)
    assert len(islands) == 1
    assert islands[0].area == pytest.approx(34 * 19)


def test_inset_l_shaped_stays_single(l_shaped_site):
    site = polygons.validate_site(l_shaped_site)
    islands = polygons.inset_islands(site, 3.0)
    assert len(islands) == 1
    assert islands[0].area < site.area


def test_inset_notched_splits_into_two(notched_site):
    site = polygons.validate_site(notched_site)
    assert len(polygons.inset_islands(site, 2.0)) == 1
    assert len(polygons.inset_islands(site, 4.0)) == 2
    assert len(polygons.inset_islands(site, 11.0)) == 0


def test_max_setback_rectangle(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    limit = polygons.max_setback(site)
    assert limit == pytest.approx(11.8)
    assert len(polygons.inset_islands(site, limit)) >= 1


def test_max_setback_notched_keeps_last_island(notched_site):
    site = polygons.validate_site(notched_site)
    limit = polygons.max_setback(site)
    assert limit == pytest.approx(7.7)
    assert len(polygons.inset_islands(site, limit)) >= 1


def test_erode_to_area(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    eroded = polygons.erode_to_area(site, 500.0)
    assert eroded.area == pytest.approx(500.0, abs=2.0)


def test_min_contour_area_rectangle(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    minimum = polygons.min_contour_area(site)
    assert 20.0 <= minimum <= 30.0


def test_validate_site_rejects_infinite():
    with pytest.raises(polygons.SiteError) as error:
        polygons.validate_site([(0.0, 0.0), (float("inf"), 0.0), (10.0, 10.0)])
    assert error.value.code == "bad_coordinates"


def test_validate_site_rejects_pinched_ring():
    pinch = [(0.0, 0.0), (10.0, 0.0), (5.0, 5.0), (10.0, 10.0), (0.0, 10.0), (5.0, 5.0)]
    with pytest.raises(polygons.SiteError) as error:
        polygons.validate_site(pinch)
    assert error.value.code == "invalid_polygon"


def test_validate_site_accepts_duplicate_consecutive_point():
    site = polygons.validate_site([(0.0, 0.0), (10.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)])
    assert site.area == pytest.approx(100.0)


def test_validate_site_accepts_clockwise_winding():
    site = polygons.validate_site([(0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0)])
    assert site.area == pytest.approx(100.0)


def test_validate_site_accepts_negative_coordinates():
    site = polygons.validate_site([(-10.0, -10.0), (10.0, -10.0), (10.0, 10.0), (-10.0, 10.0)])
    assert site.area == pytest.approx(400.0)


def test_validate_site_area_boundary():
    site = polygons.validate_site([(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)])
    assert site.area == pytest.approx(20.0)
    with pytest.raises(polygons.SiteError) as error:
        polygons.validate_site([(0.0, 0.0), (4.9, 0.0), (4.9, 4.0), (0.0, 4.0)])
    assert error.value.code == "site_too_small"


def test_inset_zero_and_negative_depth(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    for depth in (0.0, -1.0):
        islands = polygons.inset_islands(site, depth)
        assert len(islands) == 1
        assert islands[0].area == pytest.approx(site.area)


def test_inset_islands_sorted_left_to_right(notched_site):
    site = polygons.validate_site(notched_site)
    islands = polygons.inset_islands(site, 4.0)
    assert len(islands) == 2
    assert islands[0].centroid.x < islands[1].centroid.x


def test_inset_filters_tiny_islands():
    barbell = [
        (0, 0),
        (20, 0),
        (20, 9),
        (26, 9),
        (26, 3),
        (32, 3),
        (32, 15),
        (26, 15),
        (26, 11),
        (20, 11),
        (20, 20),
        (0, 20),
    ]
    site = polygons.validate_site([(float(x), float(y)) for x, y in barbell])
    assert len(polygons.inset_islands(site, 1.0)) == 2
    islands = polygons.inset_islands(site, 2.0)
    assert len(islands) == 1
    assert islands[0].area == pytest.approx(256.0, rel=0.02)


def test_max_setback_small_square():
    site = polygons.validate_site([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)])
    assert polygons.max_setback(site) == pytest.approx(2.7)


def test_max_setback_l_shaped(l_shaped_site):
    site = polygons.validate_site(l_shaped_site)
    assert polygons.max_setback(site) == pytest.approx(9.1)


def test_max_setback_boundary_invariant(rectangle_site, l_shaped_site, notched_site):
    for points in (rectangle_site, l_shaped_site, notched_site):
        site = polygons.validate_site(points)
        limit = polygons.max_setback(site)
        assert len(polygons.inset_islands(site, limit)) >= 1
        assert len(polygons.inset_islands(site, limit + 0.2)) == 0


def test_erode_identity_when_target_not_smaller(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    assert polygons.erode_to_area(site, 2000.0).area == pytest.approx(site.area)


def test_erode_tiny_target(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    eroded = polygons.erode_to_area(site, 1.0)
    assert eroded.area == pytest.approx(1.0, abs=1.0)


def test_erode_concave_hits_target(l_shaped_site):
    site = polygons.validate_site(l_shaped_site)
    assert polygons.erode_to_area(site, 200.0).area == pytest.approx(200.0, rel=0.01)


def test_erode_monotonic(rectangle_site):
    site = polygons.validate_site(rectangle_site)
    assert polygons.erode_to_area(site, 600.0).area > polygons.erode_to_area(site, 300.0).area


def test_min_contour_on_notched_island(notched_site):
    site = polygons.validate_site(notched_site)
    island = polygons.inset_islands(site, 4.0)[0]
    assert polygons.min_contour_area(island) == pytest.approx(21.2, abs=1.0)


def test_min_contour_on_l_shaped(l_shaped_site):
    site = polygons.validate_site(l_shaped_site)
    assert 15.0 <= polygons.min_contour_area(site) <= 30.0
