# PCT GeoGuesser Testing Guide

This directory contains an isolated test suite for PCT GeoGuesser. It does not
edit the application, photo catalog, generated pages, database schema, or
deployment directory.

The goal is modest and practical: catch important regressions without turning
the project into a testing hobby.

## First-time setup

From the project root:

```sh
./testing/setup.sh
```

This creates:

- `testing/.venv/` — an isolated Python environment
- `testing/.playwright-browsers/` — an isolated Chromium installation

Both directories are ignored by Git and can be deleted and recreated at any
time.

## Running tests

```sh
# Fast checks for Python utilities and photos.csv
./testing/test.sh quick

# The complete local suite, including Chromium
./testing/test.sh

# Browser tests only
./testing/test.sh browser
```

Start with `quick` while editing photo-processing logic or catalog data. Run the
complete suite before deploying.

## The four test types

### Unit tests

Unit tests check a small piece of logic in isolation. Here they cover GPS
interpolation and map URL generation.

Good unit tests are:

- fast;
- deterministic;
- specific about one behavior;
- independent of a browser, database, and network.

Example:

```python
def test_map_url_places_longitude_before_latitude(geo):
    url = geo.map_url(46.123456, -121.654321)
    assert "center=-121.654321,46.123456" in url
```

### Data-contract tests

These treat `misc/photos.csv` like an interface. They check that every row has
the shape the game expects: unique IDs, usable miles, valid sections, complete
map links, and enough photos to build a game.

They do not rewrite the CSV.

### Integration tests

Integration tests run real project scripts with several pieces connected.

The build and photo-generator tests first copy the required files into a
pytest-managed temporary directory. The scripts may write freely there without
touching the actual project.

This is preferable to duplicating the implementation inside a test.

### Browser tests

Browser tests load the temporary build in Chromium and use the app as a player
would. They cover scoring JavaScript, photo selection, practice rounds, timeout,
recap, replay, and mobile layout.

Remote photo and logo requests are redirected to existing local assets.
Supabase requests are stubbed. Production data is never read or changed.

## How tests are organized

```text
testing/
├── unit/
├── data/
├── integration/
├── browser/
├── review/
├── conftest.py
└── pytest.ini
```

`conftest.py` contains shared fixtures. A fixture prepares reusable test state,
such as the photo rows, temporary build, local web server, or safe browser
routes.

Keep a fixture only when multiple tests need the same setup. Ordinary setup that
is unique to one test should stay inside that test.

## Naming tests

Use names that finish this sentence:

> This test proves that...

Good:

- `test_guess_within_three_miles_gets_full_credit`
- `test_generator_preserves_existing_id_and_manual_metadata`
- `test_mobile_game_controls_fit_without_horizontal_overflow`

Less useful:

- `test_game`
- `test_working`
- `test_number_3`

Each test should have one clear reason to fail. Several closely related
assertions are fine when they describe one behavior.

## Adding a regression test

When a bug is found:

1. Identify the smallest public behavior that demonstrates it.
2. Add a test that fails because of the bug.
3. Confirm the failure message makes sense.
4. Fix the application.
5. Run the test again and keep it permanently.

That test is now a regression test: it prevents the same bug from quietly
returning.

Choose the lowest-cost test level that proves the fix:

- calculation or parser bug → unit test;
- malformed photo row → data test;
- build or script behavior → integration test;
- interaction or layout bug → browser test.

## Understanding failures

Pytest prints:

1. the failing test name;
2. the source line that failed;
3. the actual and expected values;
4. a short summary at the end.

Run one failing test directly while debugging:

```sh
testing/.venv/bin/python -m pytest \
  -c testing/pytest.ini \
  testing/browser/test_journeys.py::test_practice_guess_shows_answer_score_direction_and_map \
  -vv
```

Useful options:

```sh
-vv        # more detail
-x         # stop after the first failure
-k mobile  # run tests whose names contain "mobile"
-s         # show print output
```

If a browser test fails, first run that test alone. Browser tests are slower and
have more moving parts than unit tests, so a focused failure is easier to read.

## Testing standards used here

- Test observable behavior, not incidental implementation details.
- Never depend on test execution order.
- Never write to production services.
- Use temporary directories for scripts that write files.
- Make randomness deterministic inside tests.
- Prefer focused assertions over snapshots of entire generated HTML files.
- Add a regression test with each future bug fix.
- Do not pursue a coverage percentage for its own sake.

The structure follows the official
[pytest good practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
and
[Playwright pytest guidance](https://playwright.dev/python/docs/test-runners).

## What is intentionally not automated

For now, Google OAuth, authenticated profile editing, scored-game writes, admin
mutations, and Supabase security controls remain manual. Automating those safely
requires a separate staging backend. See `FUTURE_AUTOMATION.md`.

