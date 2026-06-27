from __future__ import annotations

import re
from collections import Counter
from urllib.parse import parse_qs, urlparse

import pytest


pytestmark = pytest.mark.data

REQUIRED_COLUMNS = {
    "id",
    "mile",
    "direction",
    "section",
    "date",
    "filename",
    "url",
    "version",
    "photo_by",
    "photo_by_url",
    "tags",
    "lat",
    "lon",
    "map",
}
VALID_SECTIONS = {
    "Southern California",
    "The Sierra",
    "Northern California",
    "Oregon",
    "Washington",
}


def expected_section(mile: float) -> str:
    if mile <= 702.1:
        return "Southern California"
    if mile <= 1092.3:
        return "The Sierra"
    if mile <= 1692.0:
        return "Northern California"
    if mile < 2147.0:
        return "Oregon"
    return "Washington"


def test_catalog_has_required_columns(photo_rows):
    assert photo_rows
    assert REQUIRED_COLUMNS <= set(photo_rows[0])


def test_ids_are_unique_five_letter_handles(photo_rows):
    ids = [row["id"] for row in photo_rows]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[a-z]{5}", photo_id) for photo_id in ids)


def test_filenames_and_urls_are_unique(photo_rows):
    filenames = [row["filename"] for row in photo_rows]
    urls = [row["url"] for row in photo_rows]
    assert len(filenames) == len(set(filenames))
    assert len(urls) == len(set(urls))
    assert all(url.startswith("https://") for url in urls)


def test_miles_are_numeric_sorted_and_on_trail(photo_rows):
    miles = [float(row["mile"]) for row in photo_rows]
    assert miles == sorted(miles)
    assert min(miles) >= 0
    assert max(miles) <= 2655.8


def test_sections_match_mile_boundaries(photo_rows):
    for row in photo_rows:
        assert row["section"] in VALID_SECTIONS
        assert row["section"] == expected_section(float(row["mile"])), row["id"]


def test_direction_version_and_tags_use_known_values(photo_rows):
    assert {row["direction"] for row in photo_rows} <= {"NoBo", "SoBo"}
    assert {row["version"] for row in photo_rows} <= {"v1-demo", "v2-scored"}
    tags = {
        tag.strip()
        for row in photo_rows
        for tag in row["tags"].split(",")
        if tag.strip()
    }
    assert tags <= {"green-tunnel"}


def test_coordinates_and_map_links_are_complete(photo_rows):
    for row in photo_rows:
        lat = float(row["lat"])
        lon = float(row["lon"])
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180

        query = parse_qs(urlparse(row["map"]).query)
        assert query["center"] == [f"{row['lon']},{row['lat']}"], row["id"]
        assert query["level"] == ["14"]


def test_each_mode_has_enough_photos_per_section(photo_rows):
    counts = Counter((row["version"], row["section"]) for row in photo_rows)
    for version in ("v1-demo", "v2-scored"):
        for section in VALID_SECTIONS:
            assert counts[(version, section)] >= 2, (version, section)


def test_fixed_practice_photos_have_expected_metadata(photos_by_id):
    opener = photos_by_id["tdlce"]
    assert (opener["mile"], opener["direction"], opener["version"]) == (
        "0",
        "SoBo",
        "v1-demo",
    )
    assert opener["photo_by"] == "First Light"

    second = photos_by_id["ikjxl"]
    assert (second["mile"], second["direction"], second["section"]) == (
        "2280.0",
        "NoBo",
        "Washington",
    )
    assert second["version"] == "v1-demo"
    assert second["photo_by"] == "Josh Sanders"

