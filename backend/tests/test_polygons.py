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
