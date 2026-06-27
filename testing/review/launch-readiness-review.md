# PCT GeoGuesser Launch-Readiness Review

Review date: June 24, 2026

## How to read this review

Evidence labels:

- **Verified** — observed in the live public app or exercised by the local suite.
- **Source review** — established from repository code, but not exploited against
  production.
- **Not exercised** — requires credentials, production writes, destructive
  actions, or a staging environment.

Priority:

- **P0** — address before wider promotion.
- **P1** — strong pre-launch recommendation.
- **P2** — worthwhile polish or post-launch hardening.

## Executive assessment

The public practice experience is cohesive, attractive, and notably good on a
phone. The game has a clear identity, useful result feedback, and enough photo
inventory for repeat play.

The largest launch risks are not visual. They sit at the trust boundary between
the browser and Supabase, and in rendering profile-controlled text as HTML.
Those should be resolved before inviting substantially more public traffic.

The new suite under `testing/` begins addressing regression risk without
changing the application.

## Findings

### P0 — Score submission trusts client-provided identity and game truth

- **Evidence:** Source review.
- **Where:** `misc/supabase_schema.sql`, `submit_game()`.
- **Observation:** The `SECURITY DEFINER` RPC accepts `p_user_id`, total score,
  perfect count, photo IDs, true miles, individual scores, and timeout flags
  from the browser. It inserts them without checking `auth.uid() =
  p_user_id`, requiring exactly ten valid photos, or independently calculating
  scores from server-owned answers.
- **Impact:** A caller may be able to forge leaderboard scores, submit on behalf
  of another profile, or corrupt photo statistics. The exact production grants
  were not probed.
- **Effort:** Medium to high.
- **Recommendation:** At minimum, require an authenticated caller matching
  `p_user_id`, exactly ten unique recognized photos, and valid field ranges.
  Prefer storing canonical photo answers server-side and calculating each score
  inside the RPC. Explicitly revoke function execution from roles that should
  not call it.
- **Acceptance test:** Staging tests prove anonymous calls, mismatched user IDs,
  unknown photos, altered true miles, altered scores, duplicates, and non-ten
  photo payloads are rejected; a valid authenticated game succeeds.

### P0 — Profile-controlled text is interpolated into `innerHTML`

- **Evidence:** Source review.
- **Where:** Leaderboard and admin row rendering, particularly
  `app-leaderboard/build.py` and `app-admin/build.py`.
- **Observation:** Trail names and PCT year values read from public profiles are
  inserted into HTML template strings. A user can update their own profile
  through the API, so client-side form controls are not a security boundary.
- **Impact:** Stored cross-site scripting could run in visitors' or the
  administrator's browser.
- **Effort:** Low to medium.
- **Recommendation:** Construct cells and links with DOM APIs and assign
  user-controlled values with `textContent`. Add server-side length and content
  constraints. Treat `about` and future social fields the same way.
- **Acceptance test:** A staging profile containing HTML metacharacters renders
  as literal text on leaderboard, hiker, and admin pages; no element or script
  is created from the value.

### P1 — The displayed post-game rank uses a different rule from the leaderboard

- **Evidence:** Source review.
- **Where:** `app-game/build.py`, `submitGameScore()`.
- **Observation:** The post-game rank counts every higher-scoring session in the
  last 90 days. The leaderboard ranks each player's best session only.
- **Impact:** Players can be shown a worse rank than the leaderboard actually
  gives them, especially when active players have multiple games.
- **Effort:** Low to medium.
- **Recommendation:** Use one server query/RPC for leaderboard rank, or fetch and
  deduplicate by player using the same rule as the leaderboard.
- **Acceptance test:** With two higher-scoring sessions belonging to one player,
  the new player's displayed rank counts that player once.

### P1 — Guess controls lack accessible names

- **Evidence:** Verified in the live DOM and source review.
- **Where:** The numeric mile input and trail slider in `app-game/build.py`.
- **Observation:** “What Mile is this?” is visual text rather than an associated
  `<label>`. Browser accessibility output exposes an unnamed spinbutton and
  slider. Result and recap images also use empty or generic alternative text.
- **Impact:** Screen-reader and voice-control users cannot reliably identify the
  primary controls.
- **Effort:** Low.
- **Recommendation:** Associate a real label with the number field, add an
  accessible slider label and value text, announce timer/result updates
  appropriately, and provide useful result-image alternatives.
- **Acceptance test:** Browser accessibility inspection reports meaningful names
  for both controls and a keyboard-only player can finish a game.

### P1 — A game eagerly downloads ten large original images

- **Evidence:** Verified from local assets and source review.
- **Observation:** The 246 deployed photos total roughly 637 MB; the average is
  about 2.6 MB and the largest is about 10 MB. `prepareNextGame()` preloads all
  ten selected originals immediately.
- **Impact:** A typical game may transfer tens of megabytes before the player
  reaches later rounds, which is costly and slow on trail/mobile connections.
- **Effort:** Medium.
- **Recommendation:** Generate appropriately sized WebP/AVIF derivatives, use
  responsive image sources, and preload only the current and next image.
- **Acceptance test:** A throttled mobile run starts promptly and total image
  transfer for one game meets an agreed budget without visibly degrading photos.

### P1 — The saved-game cap becomes a permanent player-facing failure

- **Evidence:** Source review; not exercised against production.
- **Where:** `enforce_session_cap()` in `misc/supabase_schema.sql`.
- **Observation:** A user is blocked after 15 saved sessions until an
  administrator deletes data. The game UI does not present this as a known limit
  or recovery path.
- **Impact:** Engaged players eventually cannot submit scores.
- **Effort:** Low to medium.
- **Recommendation:** Remove the cap, retain only a rolling history, or clearly
  implement an automatic replacement/retention policy.
- **Acceptance test:** A player can continue playing after the chosen retention
  threshold and leaderboard/history behavior remains predictable.

### P1 — Regression coverage was absent

- **Evidence:** Verified repository inspection.
- **Observation:** Scoring, selection, build output, and core browser journeys
  previously had no automated checks.
- **Impact:** Small edits to large generated HTML scripts can silently break
  multiple modes.
- **Effort:** Addressed initially.
- **Recommendation:** Use the suite in `testing/` before deployments and add a
  regression test with each bug fix.
- **Acceptance test:** `./testing/test.sh` passes from a fresh setup.

### P2 — Practice mode always starts with the same two photos

- **Evidence:** Verified by source and browser tests.
- **Observation:** Mile 0 is always first and the Josh Sanders Washington photo
  is always second.
- **Impact:** The first 20% of every practice game becomes predictable, reducing
  replay value and making practice scores less comparable to scored mode.
- **Effort:** Low.
- **Recommendation:** Keep a guided first game if desired, then randomize later
  practice games or rotate among a small set of approachable openers.
- **Acceptance test:** Repeat players receive varied early rounds while a new
  player still gets a comprehensible introduction.

### P2 — Practice fallback selection can exceed the green-tunnel cap

- **Evidence:** Verified by deterministic Chromium testing.
- **Observation:** The intended maximum is two `green-tunnel` photos, but the
  fallback path relaxes the cap and some valid random seeds produce three.
- **Impact:** A game can contain more visually repetitive or difficult forest
  scenes than intended.
- **Effort:** Low.
- **Recommendation:** Exhaust all non-green-tunnel candidates across the section
  before relaxing the global cap, and include fixed photos in the final
  invariant check.
- **Acceptance test:** The currently expected-failure browser test
  `test_practice_selection_never_exceeds_green_tunnel_cap` passes across its
  deterministic seed set.

### P2 — The photo catalog is overwhelmingly NoBo

- **Evidence:** Verified data review.
- **Observation:** 238 of 246 catalog rows are NoBo and 8 are SoBo.
- **Impact:** Direction is presented as a gameplay clue but provides little
  variety. The imbalance may also shape which seasonal/visual patterns players
  learn.
- **Effort:** Content-dependent.
- **Recommendation:** Treat this as a documented catalog limitation, then add
  SoBo and non-summer photos when suitable contributions are available.
- **Acceptance test:** Track direction and season distribution in the admin
  catalog and set a realistic content target rather than forcing artificial
  balance.

### P2 — The About link does not lead to About content

- **Evidence:** Verified in the live landing page.
- **Observation:** The footer's About link points back to `/`.
- **Impact:** Minor trust and completeness issue.
- **Effort:** Low.
- **Recommendation:** Add the planned About page or remove the link until it
  exists.
- **Acceptance test:** The link opens a page explaining the project, photo
  sources, scoring, privacy, and contact/reporting route.

### P2 — Public read policies expose more game detail than public pages need

- **Evidence:** Source review; production grants not probed.
- **Where:** Public read policies for `game_sessions` and `game_guesses`.
- **Observation:** Individual guesses and session rows are readable, while the
  public product mainly needs aggregate leaderboard and profile information.
- **Impact:** Unnecessary exposure increases privacy and scraping surface.
- **Effort:** Medium.
- **Recommendation:** Expose purpose-built read views/RPCs containing only the
  fields needed by public pages; restrict raw guesses where practical.
- **Acceptance test:** Public pages work through limited interfaces and anonymous
  callers cannot enumerate unnecessary raw gameplay records.

## Suggested order

1. Secure `submit_game()` and remove stored-XSS paths.
2. Fix rank consistency and decide the saved-game retention policy.
3. Add control labels and keyboard/accessibility checks.
4. Reduce image transfer.
5. Adopt the local test suite as a pre-deployment habit.
6. Address content variety and small completeness issues.

## Areas intentionally not exercised

- Google OAuth completion.
- Authenticated profile writes.
- Scored-game database writes and limits.
- Admin search, edits, settings, and deletion.
- Direct RLS/RPC abuse attempts.
- Destructive data-maintenance workflows.
- Load, concurrency, and formal penetration testing.

Use `manual-checklist.md` for safe current checks and
`../FUTURE_AUTOMATION.md` for the later staging plan.
