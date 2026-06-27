from __future__ import annotations

import pytest

from helpers import load_module


pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def geo(project_root):
    return load_module(
        project_root / "misc" / "add_geo_columns.py",
        "pct_add_geo_columns_for_tests",
    )


def test_interpolate_returns_exact_waypoint(geo):
    points = [(0.0, 32.0, -117.0), (10.0, 34.0, -119.0)]
    assert geo.interpolate(points, [0.0, 10.0], 10.0) == (34.0, -119.0)


def test_interpolate_finds_midpoint(geo):
    points = [(0.0, 32.0, -117.0), (10.0, 34.0, -119.0)]
    assert geo.interpolate(points, [0.0, 10.0], 5.0) == (33.0, -118.0)


def test_interpolate_clamps_below_and_above_range(geo):
    points = [(10.0, 33.0, -118.0), (20.0, 35.0, -120.0)]
    miles = [10.0, 20.0]
    assert geo.interpolate(points, miles, -1.0) == (33.0, -118.0)
    assert geo.interpolate(points, miles, 99.0) == (35.0, -120.0)


def test_interpolate_handles_duplicate_reference_miles(geo):
    points = [
        (0.0, 30.0, -110.0),
        (10.0, 40.0, -120.0),
        (10.0, 41.0, -121.0),
    ]
    assert geo.interpolate(points, [0.0, 10.0, 10.0], 10.0) == (40.0, -120.0)


def test_map_url_places_longitude_before_latitude(geo):
    url = geo.map_url(46.123456, -121.654321)
    assert "center=-121.654321,46.123456" in url
    assert url.endswith("&level=14")

