# Deferred Staging and Automation Plan

This is deliberately a later phase. The current local suite should become
familiar and useful before adding infrastructure.

## 1. Create an isolated Supabase staging project

- Apply the schema and RPCs to a separate Supabase project.
- Use a different URL, anon key, OAuth configuration, and admin identity.
- Add a prominent `STAGING` marker to fixture trail names and data.
- Never copy production authentication users or personal profile text.

## 2. Create a staging Cloudflare Pages site

- Build the same static application with staging Supabase configuration.
- Use a separate Pages project and hostname.
- Configure Google OAuth redirects only for the staging hostname.
- Add a visible staging banner to prevent confusing it with production.

## 3. Add disposable fixture accounts and data

- Create one ordinary player, one second player for ranking, and one admin.
- Seed known profiles, games, guesses, photo statistics, and settings.
- Provide a reset script that restores the fixtures before a test run.
- Store no passwords, tokens, or service-role keys in the repository.

## 4. Add staging-only security and write tests

Mark every such test with `@pytest.mark.staging`. Cover:

- a user can write only their own profile;
- anonymous and mismatched users cannot submit games;
- forged totals, true miles, photo IDs, scores, and photo counts are rejected;
- rate and session limits behave as intended;
- leaderboard and profile statistics update after a valid game;
- non-admin users cannot call admin RPCs;
- admin RPCs update only their intended records;
- deleting games leaves aggregate photo statistics consistent.

These tests should be safe to rerun and should never point at production.

## 5. Add GitHub Actions gradually

Start with a small workflow:

1. check out the repository;
2. install Python dependencies;
3. run `./testing/test.sh quick`;
4. run build integration tests.

Once that is reliable, install Chromium and add the small browser suite. Do not
add staging tests to pull requests until fixture reset and secret handling are
proven.

## 6. Handle secrets and test artifacts safely

- Store staging URLs, keys, and account credentials as GitHub repository
  secrets.
- Restrict staging service-role credentials to reset/setup jobs only.
- Keep production credentials out of automation.
- Upload Playwright traces only when a browser test fails.
- Use short artifact retention.
- Rotate a secret immediately if it appears in logs.

## Suggested trigger order

1. Local suite is stable and routinely used.
2. Quick tests run automatically on pushes and pull requests.
3. Chromium tests run automatically.
4. Staging read tests run on demand.
5. Staging write/security tests run on demand or on protected branches.

This order captures most of the value before accepting the operational overhead
of staging.

