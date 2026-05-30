# PCT GeoGuesser — TODO

This doc outlines our goals, what we've planned to do, and what we've done.

## Goal

GeoGuesser-style game for PCT hikers. Players guess the trail mile from a photo.
Two modes: practice (no login) and scored (Google login, global leaderboard).

Hosted on Cloudflare Pages. Backend: Supabase (PostgreSQL + Google OAuth).

---

## To Do / Up Next / Ideas / future work
- About page (`/about/`) — landing page "About PCT GeoGuesser" link points here
- Photo stats recalculation tool in admin (after bulk deletes)
- More photos / photo reassignment before launch
- Social links on hiker profile page (requires new `social_links` columns in profiles)

---

## Sorted

### ✅ Polish + Anti-Cheat (2026-05-30)

- **Back-nav anti-cheat guard:** `pageshow` listener detects bfcache restores (`e.persisted = true`) during an active game. Stops timer, wipes state, returns to start screen, shows "Game Interrupted" modal. `history.replaceState()` flushes bfcache so forward navigation does a clean reload. Applies to both modes.
- **Leaderboard consolidated:** `/leaderboard/all-time/` removed. `/leaderboard/` is the only URL, defaults to All-Time. 90-Day tab appears only when enabled in Admin → Site Settings.
- **Admin Site Settings tab (4th tab):** Toggle to show/hide 90-Day leaderboard. Saves via `admin_set_setting()` RPC. Persists in new `site_settings` table.
- **Supabase:** `site_settings` table + `admin_set_setting()` SECURITY DEFINER RPC added.
- **Timer:** 30s → 45s across game, landing page, README.
- **Green-tunnel cap:** 3 → 2 per game (both modes).
- **`app-game/build.py` docs:** Comprehensive header block covering all key JS functions.
- **Admin Recent Games:** Score rounded to 1 decimal.
- **Lightbox caption:** `photo_by` on its own line.
- **Duplicate profile fix:** Stale UUID orphan removed from admin Edit Database.

---

### ✅ Launch + Post-Launch Fixes (2026-05-29)

- **Photos:** 42 new Washington photos added (miles 2467–2655), 245 total. v1-demo pool reduced. Green-tunnel cap enforced.
- **Deployed to production:** Wiped Supabase game_sessions, deployed via wrangler, smoke-tested.
- **DB schema fix — float scores:** `total_score` + `score` columns changed `INTEGER` → `NUMERIC`. Stale RPC overload dropped.
- **File structure:** Raw photos moved from external drive to `img/raw-photos-save/`. All paths now relative.
- **Admin duplicate player fix:** Stale profile row removed.

---

### ✅ Scoring Overhaul + UI Polish

- **New scoring system** (highest score wins): exponential decay formula, max 2655.8 pts, ±3 mi grace zone, timeout = 0 pts.
- **`photo_by` credit field:** Shown in hints, result screen, end table, lightbox.
- **Hiker profile hero card:** Big best score, tier-based callout text, ranking badges.
- **Admin Photo Stats:** Date + Photo By columns.
- **Leaderboard:** Descending sort, pts units.
- **`app-game/` consolidation:** Merged `app-game-v1-practice` + `app-game-v2-scored` → single `build.py` with `make_html(mode)`.
- **Database reset:** `game_sessions`, `game_guesses`, `photo_stats` wiped. Schema updated.

---

### ✅ First Init and testing version

- Init basic photo-explorer app
- Photo anonymisation — random IDs, CSV with mile/direction/section metadata
- Mobile improvements — full-screen image, pinch-to-zoom, responsive nav
- Practice game (v1) — timer, slider, scoring, result + end screens
- Game polish — tri-colour slider dot, preload, pinch-to-zoom, Futura font, OG tags
- Supabase setup — Google OAuth, schema (tables, RLS, rate-limit triggers, RPCs)
- Landing page (`/`), practice at `/practice/`, scored game at `/game/`
- Leaderboard pages (`/leaderboard/`)
- Hiker profile page (`/hiker/?id=<uuid>`)
- Admin dashboard (`/admin/`) — Recent Games, Photo Stats, Edit Database
- Profile editing from game start screen
- Practice game: Mile 1 (tdlce) always shown first
- SQL: rate limit 5 min → 1 min; session cap → 10 (later 15)
