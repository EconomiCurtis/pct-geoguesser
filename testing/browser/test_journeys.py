from __future__ import annotations

import pytest


pytestmark = pytest.mark.browser


def test_landing_page_links_to_primary_destinations(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/")

    assert page.get_by_role("link", name="Practice Game →").get_attribute("href") == "/practice/"
    assert page.get_by_role("link", name="Scored Game →").get_attribute("href") == "/game/"
    assert page.get_by_role("link", name="Leaderboard").get_attribute("href") == "/leaderboard/"


def test_scored_game_shows_login_and_practice_fallback(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/game/")

    page.locator("#screen-auth").wait_for(state="visible")
    assert page.get_by_role("button", name="Sign in with Google").is_visible()
    assert page.get_by_role("link", name="Try Practice Mode").get_attribute("href") == "/practice/"


def test_practice_guess_shows_answer_score_direction_and_map(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/practice/")
    page.locator("#screen-guess").wait_for(state="visible")

    page.locator("#mile-input").fill("100")
    page.get_by_role("button", name="Submit →").click()
    page.locator("#screen-result").wait_for(state="visible")

    assert page.locator("#r-your-guess").inner_text() == "100"
    assert page.locator("#r-true-mile").inner_text() == "0"
    assert "100 Miles North" in page.locator("#st-verdict").inner_text()
    assert page.locator("#st-round").inner_text().startswith("184.3")
    assert page.locator("#r-map-link").get_attribute("href").startswith("https://pcta.maps.arcgis.com/")


def test_timeout_can_be_exercised_without_waiting_sixty_seconds(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/practice/")
    page.locator("#screen-guess").wait_for(state="visible")

    page.evaluate("processGuess(null, true)")
    page.locator("#screen-result").wait_for(state="visible")

    assert page.locator("#r-your-guess").inner_text() == "—"
    assert page.locator("#st-verdict").inner_text() == "Timed out"
    assert page.locator("#st-round").inner_text().startswith("0.0")


def test_complete_practice_game_reaches_recap_and_can_replay(local_app):
    page, base_url = local_app
    page.goto(f"{base_url}/practice/")

    for round_number in range(10):
        page.locator("#screen-guess").wait_for(state="visible")
        page.locator("#mile-input").fill("0")
        page.get_by_role("button", name="Submit →").click()
        page.locator("#screen-result").wait_for(state="visible")
        expected = "See Final Results →" if round_number == 9 else "Next Photo →"
        page.get_by_role("button", name=expected).click()

    page.locator("#screen-end").wait_for(state="visible")
    assert page.locator("#end-tbody tr").count() == 10
    assert page.locator("#final-score").inner_text()
    assert page.get_by_role("link", name="Try the Scored Game →").is_visible()

    page.get_by_role("button", name="Practice Again").click()
    page.locator("#screen-guess").wait_for(state="visible")
    assert page.locator("#g-cur").inner_text() == "1"


def test_mobile_game_controls_fit_without_horizontal_overflow(local_app):
    page, base_url = local_app
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{base_url}/practice/")
    page.locator("#screen-guess").wait_for(state="visible")

    layout = page.evaluate(
        """() => {
          const input = document.querySelector("#mile-input").getBoundingClientRect();
          const submit = document.querySelector('button[onclick="submitGuess()"]').getBoundingClientRect();
          return {
            scrollWidth: document.documentElement.scrollWidth,
            viewportWidth: window.innerWidth,
            inputWidth: input.width,
            submitWidth: submit.width,
            inputLeft: input.left,
            submitRight: submit.right
          };
        }"""
    )

    assert layout["scrollWidth"] <= layout["viewportWidth"] + 1
    assert layout["inputWidth"] >= 150
    assert layout["submitWidth"] >= 90
    assert layout["inputLeft"] >= 0
    assert layout["submitRight"] <= layout["viewportWidth"]

