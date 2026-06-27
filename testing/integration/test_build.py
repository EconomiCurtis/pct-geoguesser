from __future__ import annotations

import csv
from pathlib import Path

import pytest

from helpers import extract_embedded_photos


pytestmark = pytest.mark.integration


def test_real_build_generates_every_deploy_page(built_project: Path):
    expected = {
        "deploy/index.html",
        "deploy/practice/index.html",
        "deploy/game/index.html",
        "deploy/leaderboard/index.html",
        "deploy/hiker/index.html",
        "deploy/admin/index.html",
    }
    generated = {
        str(path.relative_to(built_project))
        for path in (built_project / "deploy").rglob("index.html")
    }
    assert expected <= generated
    assert all((built_project / path).stat().st_size > 1_000 for path in expected)


def test_generated_game_pages_embed_the_correct_photo_pools(built_project: Path):
    with (built_project / "misc" / "photos.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    practice_html = (built_project / "deploy" / "practice" / "index.html").read_text()
    scored_html = (built_project / "deploy" / "game" / "index.html").read_text()
    practice = extract_embedded_photos(practice_html)
    scored = extract_embedded_photos(scored_html)

    assert {photo["id"] for photo in practice} == {
        row["id"] for row in rows if row["version"] == "v1-demo"
    }
    assert {photo["id"] for photo in scored} == {
        row["id"] for row in rows if row["version"] == "v2-scored"
    }


def test_generated_pages_use_canonical_metadata_and_test_backend(built_project: Path):
    landing = (built_project / "deploy" / "index.html").read_text()
    practice = (built_project / "deploy" / "practice" / "index.html").read_text()
    scored = (built_project / "deploy" / "game" / "index.html").read_text()

    assert 'content="https://pct-geoguesser.economicurtis.com/"' in landing
    assert 'content="https://pct-geoguesser.economicurtis.com/practice/"' in practice
    assert 'content="https://pct-geoguesser.economicurtis.com/game/"' in scored
    assert "https://testing.invalid" in scored
    assert "test-anon-key" in scored

