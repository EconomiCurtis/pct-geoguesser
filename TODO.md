# PCT GeoGuesser — TODO

This doc outlines our goals, what we've planned to do, and what we've done.
It will eventually be superseded by the GitHub repo's pull request log once
the project moves there.

## Goal

GeoGuesser-style game for PCT hikers. Players guess the trail mile from a photo.
Two modes: practice (no login) and scored (Google login, global leaderboard).

Hosted on Cloudflare Pages. Backend: Supabase (PostgreSQL + Google OAuth).

---

## To Do

(all steps complete — see ideas below)

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
