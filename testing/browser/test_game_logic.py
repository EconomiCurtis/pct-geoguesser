from __future__ import annotations

from collections import Counter

import pytest


pytestmark = pytest.mark.browser

SECTIONS = {
    "Southern California",
    "The Sierra",
    "Northern California",
    "Oregon",
    "Washington",
}

SEEDED_SELECTIONS = """
(seeds) => {
  const originalRandom = Math.random;
  function seeded(seed) {
    let state = seed >>> 0;
    return function () {
      state = (Math.imul(1664525, state) + 1013904223) >>> 0;
      return state / 4294967296;
    };
  }
  const selections = seeds.map(seed => {
    Math.random = seeded(seed);
    return selectGamePhotos().map(p => ({
      id: p.id,
      mile: Number(p.mile),
      section: p.section,
      tags: p.tags || ""
    }));
  });
  Math.random = originalRandom;
  return selections;
}
"""


def test_scoring_uses_full_credit_then_exponential_decay(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/practice/")
    page.locator("#screen-guess").wait_for(state="visible")
    page.evaluate("stopTimer()")

    scores = page.evaluate(
        """() => ({
          exact: calcScore(100, 100),
          edge: calcScore(103, 100),
          outside: calcScore(104, 100),
          far: calcScore(600, 100),
          perfectEdge: isPerfect(103, 100),
          perfectOutside: isPerfect(104, 100)
        })"""
    )

    assert scores["exact"] == pytest.approx(265.58)
    assert scores["edge"] == pytest.approx(scores["exact"])
    assert scores["outside"] < scores["edge"]
    assert scores["far"] < scores["outside"]
    assert scores["perfectEdge"] is True
    assert scores["perfectOutside"] is False


def test_practice_selection_has_fixed_openers_and_balanced_sections(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/practice/")
    page.locator("#screen-guess").wait_for(state="visible")
    page.evaluate("stopTimer()")

    selections = page.evaluate(SEEDED_SELECTIONS, [1, 2, 3, 4, 5])
    for photos in selections:
        assert len(photos) == 10
        assert len({photo["id"] for photo in photos}) == 10
        assert photos[0]["id"] == "tdlce"
        assert photos[1]["id"] == "ikjxl"
        assert Counter(photo["section"] for photo in photos) == {
            section: 2 for section in SECTIONS
        }


@pytest.mark.xfail(
    reason="Known app issue: practice fallback selection can exceed the cap of two",
    strict=False,
)
def test_practice_selection_never_exceeds_green_tunnel_cap(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/practice/")
    page.locator("#screen-guess").wait_for(state="visible")
    page.evaluate("stopTimer()")

    selections = page.evaluate(SEEDED_SELECTIONS, list(range(1, 50)))
    for photos in selections:
        green_tunnels = sum(
            "green-tunnel" in photo["tags"].split(",") for photo in photos
        )
        assert green_tunnels <= 2


def test_practice_random_pairs_respect_section_spacing(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/practice/")
    page.locator("#screen-guess").wait_for(state="visible")
    page.evaluate("stopTimer()")

    selections = page.evaluate(SEEDED_SELECTIONS, list(range(20, 40)))
    for photos in selections:
        for section in ("The Sierra", "Northern California", "Oregon"):
            miles = [photo["mile"] for photo in photos if photo["section"] == section]
            assert len(miles) == 2
            assert abs(miles[0] - miles[1]) >= 20


def test_scored_selection_is_balanced_unique_and_spaced(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/game/")
    page.locator("#screen-auth").wait_for(state="visible")

    selections = page.evaluate(SEEDED_SELECTIONS, list(range(50, 70)))
    for photos in selections:
        assert len(photos) == 10
        assert len({photo["id"] for photo in photos}) == 10
        assert Counter(photo["section"] for photo in photos) == {
            section: 2 for section in SECTIONS
        }
        assert sum("green-tunnel" in photo["tags"].split(",") for photo in photos) <= 2
        for section in SECTIONS:
            miles = [photo["mile"] for photo in photos if photo["section"] == section]
            assert abs(miles[0] - miles[1]) >= 20
