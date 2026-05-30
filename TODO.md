# PCT GeoGuesser — TODO

This doc outlines our goals, what we've planned to do, and what we've done.
It will eventually be superseded by the GitHub repo's pull request log once
the project moves there.

## Goal

GeoGuesser-style game for PCT hikers. Players guess the trail mile from a photo.
Two modes: practice (no login) and scored (Google login, global leaderboard).

Hosted on Cloudflare Pages. Backend: Supabase (PostgreSQL + Google OAuth).

---

## Up Next



---

## Recently Completed — Launch + Post-Launch Fixes (2026-05-29)

### ✅ Photos update
- [X] Add more photos for Washington and Oregon
- [X] Reduce v1-demo photo pool to ~40 (edit photos.csv: change ~62 rows from `v1-demo` → `v2-scored`)
- [X] Tag green-tunnel photos in photos.csv (dense forest, no visible landmarks), limit number of these in each game to <=2. 


### ✅ Deployed to production
- [x] Wiped Supabase game_sessions (old scores used miles-off system, incompatible with new pts)
- [x] Deployed via `npx wrangler pages deploy deploy/ --project-name=pct-geoguesser`
- [x] Smoke-tested live site — practice game, scored game, leaderboard, hiker page all working

### ✅ DB schema fix — float scores
Old `submit_game()` RPC had `p_total_score INTEGER` and `score::INTEGER` cast, causing
`invalid input syntax for type integer` error when saving exponential-decay scores (floats).
Fixed by altering `game_sessions.total_score` and `game_guesses.score` to `NUMERIC`,
updating `submit_game()` parameter and cast, and dropping the stale INTEGER overload.

### ✅ Lightbox caption — photo_by on its own line
In both `/game` result screen and `/admin` photo stats lightbox, the `photo_by` credit
now appears on a second line below the mile/section/direction/date meta.

### ✅ Admin duplicate player fix
"First Light" had two `profiles` rows (old auth UUID orphaned after re-login).
Deleted stale row; confirmed no other duplicates.

### ✅ File structure reorganisation
Raw photos moved from external drive to `img/raw-photos-save/Summer 2025/` inside the repo.
Updated `misc/copy_rename_photos.py`, `misc/generate_photo_csv.py`, and
`app-explore/build_webapp.py` to use relative paths — no more hardcoded external drive paths.

---

## Recently Completed — Scoring Overhaul + UI Polish

### ✅ New Scoring System (highest score wins)

**Formula:**
```
S_photo = (2655.8 / N) × e^(−10 × d_eff / 2655.8)
```
- **N** = 10 photos → per-photo max = **265.58 pts**
- **Total max = 2655.8 pts** (the PCT's exact mileage — intentional easter egg)
- **Grace zone**: `d_eff = max(0, |guess − actual| − 3)` — within ±3 miles = full credit
- **Timeout** = 0 pts for that round

### ✅ Code Changes Completed

- [x] `app-game-v2-scored/build.py` — exponential scoring, photo_by chips, end-table credit, UI fixes
- [x] `app-game-v1-practice/build.py` — same scoring + UI changes as game-v2
- [x] `app-leaderboard/build.py` — `ascending: false`, pts units, updated copy
- [x] `app-hiker/build.py` — hero score card with callout text + leaderboard ranking badges
- [x] `app-admin/build.py` — Date + Photo By columns in Photo Stats
- [x] Renamed `app-game-v1-testing` → `app-game-v1-practice`
- [x] Renamed `app-game-v2` → `app-game-v2-scored`
- [x] Updated `build.sh`, `.gitignore`, `README.md`, and sub-READMEs

### ✅ `photo_by` Credit Field

- [x] Shown in active round hints area (alongside season/direction chips)
- [x] Shown on result screen — own line below the meta chips row
- [x] Shown in end-table thumbnail sub-line (photo_by only; date stays in lightbox caption)
- [x] Lightbox caption includes date + photo_by
- [x] Admin Photo Stats table: Date + Photo By columns added

### ✅ Hiker Profile Hero Card

- [x] Big best score, callout text (random, tier-based), ranking badges
- [x] Support stats (games played, avg score, total perfects) below
- [x] 7 callout options for top tier, multiple options per tier

### 🗄️ Database Reset ✅ Done 2026-05-29

Old scores (miles-off totals, lower=better) were incompatible with new scores (pts, higher=better).
`profiles` table was unaffected. `game_sessions`, `game_guesses`, and `photo_stats` wiped.
Schema updated: `total_score` and `score` columns changed from `INTEGER` → `NUMERIC`.

---

## Ideas / future work
- About page (`/about/`) — landing page "About PCT GeoGuesser" link points here
- Photo stats recalculation tool in admin (after bulk deletes)
- More photos / photo reassignment before launch
- Social links on hiker profile page (requires new `social_links` columns in profiles)

---

## Sorted

- [x] Init basic photo-explorer app
- [x] Photo anonymisation — random IDs, CSV with mile/direction/section metadata
- [x] Mobile improvements — full-screen image, pinch-to-zoom, responsive nav
- [x] Build practice game (v1) — timer, slider, scoring, result + end screens
- [x] Game polish — tri-colour slider dot, GC-safe preload, pinch-to-zoom, Futura font, OG tags
- [x] Rename `game-v1/` → `app-game-v1-testing/`, update READMEs
- [x] Update "How to Play" card — three sections, bold key points, About link placeholder
- [x] Supabase project setup — project created, Google OAuth, API keys noted (Step 1)
- [x] Schema design — photo_stats with Welford variance/SD, RLS, rate-limit triggers
- [x] Step 2 — Supabase schema live (tables, RLS, triggers, RPC)
- [x] Step 3 — Landing page (`/`), v1 practice game moved to `/practice/`
- [x] Step 4 — v2 scored game at `/game/` (Google login, signup, submit_game RPC, rank display)
- [x] Step 5 — Leaderboard pages (`/leaderboard/` 90-day + `/leaderboard/all-time/`)
- [x] Step 6 — Hiker profile page (`/hiker/?id=<uuid>`)
- [x] Admin dashboard (`/admin/`) — three tabs:
  - **Recent Games** — last 100 scored games with player links and timestamps
  - **Photo Stats** — per-photo appearance count, average error, SD (Welford's algorithm)
  - **Edit Database** — player search; inline name editing; delete games or full player
- [x] Hiker profile links from leaderboard, admin, and game greeting
- [x] Edit profile (about text) from the game start screen
- [x] Bug fix — game_guesses/photo_stats mismatch caused by `prepareNextGame()` overwriting
      `gamePhotos` before `submitGameScore()` captured the payload
- [x] Practice game: Mile 1 always shown first (easy opener), remaining 9 random by section
- [x] SQL: rate limit reduced 5 min → 1 min; session cap reduced 500 → 10
- [x] Scoring overhaul — highest-score-wins, exponential decay, max 2655.8 pts
- [x] `photo_by` credit field — shown in hints, result screen, end table, lightbox
- [x] Hiker profile hero card — big score, callout text (7 tiers, random pick), ranking badges
- [x] Admin Photo Stats — Date + Photo By columns
- [x] `app-game-v1-testing` → `app-game-v1-practice` rename (later merged)
- [x] `app-game-v2` → `app-game-v2-scored` rename (later merged)
- [x] Merged `app-game-v1-practice` + `app-game-v2-scored` → single `app-game/build.py` with `make_html(mode)`
- [x] final-avg line: "On average, your guesses were X miles off"
- [x] Result screen photo_by: own line below meta chips
