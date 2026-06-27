from __future__ import annotations

import csv
import shutil
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.integration

FIELDNAMES = [
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
]


def make_pipeline_project(tmp_path: Path, project_root: Path) -> tuple[Path, Path]:
    project = tmp_path / "pipeline-project"
    misc = project / "misc"
    photos = project / "img" / "raw-photos-save" / "Summer 2025"
    misc.mkdir(parents=True)
    photos.mkdir(parents=True)
    shutil.copy2(project_root / "misc" / "generate_photo_csv.py", misc)
    return project, photos


def run_generator(project: Path) -> list[dict[str, str]]:
    result = subprocess.run(
        ["python3", "misc/generate_photo_csv.py"],
        cwd=project,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    with (project / "misc" / "photos.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_generator_extracts_mile_direction_section_and_url(tmp_path, project_root):
    project, photos = make_pipeline_project(tmp_path, project_root)
    (photos / "Trail view Mile 800.4 SoBo.jpeg").touch()

    rows = run_generator(project)

    assert len(rows) == 1
    row = rows[0]
    assert row["mile"] == "800.4"
    assert row["direction"] == "SoBo"
    assert row["section"] == "The Sierra"
    assert row["version"] == "v2-scored"
    assert row["url"].endswith(f"/{row['id']}.jpeg")


def test_generator_skips_files_without_a_mile(tmp_path, project_root):
    project, photos = make_pipeline_project(tmp_path, project_root)
    (photos / "pretty trail but no location.jpeg").touch()

    rows = run_generator(project)

    assert rows == []


def test_generator_preserves_existing_id_and_manual_metadata(tmp_path, project_root):
    project, photos = make_pipeline_project(tmp_path, project_root)
    filename = "Existing Mile 1200 NoBo.jpeg"
    (photos / filename).touch()
    existing = {
        "id": "abcde",
        "mile": "1200.0",
        "direction": "NoBo",
        "section": "Northern California",
        "date": "Spring 2024",
        "filename": filename,
        "url": "https://old.invalid/photo.jpeg",
        "version": "v1-demo",
        "photo_by": "A Hiker",
        "photo_by_url": "https://example.com/hiker",
        "tags": "green-tunnel",
        "lat": "40.1",
        "lon": "-121.2",
        "map": "https://example.com/map",
    }
    with (project / "misc" / "photos.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerow(existing)

    rows = run_generator(project)

    assert len(rows) == 1
    row = rows[0]
    for field in (
        "id",
        "mile",
        "direction",
        "section",
        "date",
        "version",
        "photo_by",
        "photo_by_url",
        "tags",
        "lat",
        "lon",
        "map",
    ):
        assert row[field] == existing[field]
    assert row["url"].endswith("/abcde.jpeg")

