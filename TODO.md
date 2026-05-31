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

### ✅ Photo Locations + Map Links + Docs (2026-05-31)

- **Photo GPS columns:** Added `lat`, `lon`, and `map` to photos.csv. Lat/lon are interpolated for each photo's trail mile against a ~2,900-point GPS waypoint spreadsheet; `map` is a PCTA interactive-map deep link centered on that point (zoom level 14).
- **`add_geo_columns.py` (new):** Reusable, documented script that fills the geo columns. Fills only blank rows by default (preserves hand-tuned values); `--force` recomputes all. Rounds lat/lon consistently to 6 dp in every branch.
- **`generate_photo_csv.py` fix:** Added `lat`/`lon`/`map` to FIELDNAMES so re-running preserves geo values instead of crashing on the extra keys. New rows leave geo blank for `add_geo_columns.py` to fill. Added a full header docblock.
- **Map links in review screens:** The post-guess result screen and the end-game recap lightbox now show a `map ↗` link (both game modes). Admin Photo Stats lightbox got the same link. A `·` separates the photo credit from the map link when both are present. The during-guess screen is untouched (no location hints while guessing).
- **rzzub correction:** Filename + mile fixed (2599.8 -> 2499.8) and re-sorted into mile order in photos.csv.
- **Leaderboard label:** "Best Score (pts)" column header shortened to "Best Score" (scores already carry "pts").
- **Documentation pass:** File-header docblocks added to `copy_rename_photos.py`, `add_geo_columns.py`, and local-only `app-explore/build_webapp.py`. Corrected the stale `app-admin` header (four tabs incl. Site Settings; photo count no longer hardcoded). README updated with the geo workflow step, the new script, the gameplay map-link note, and a fixed `/` footer description.

---

### ✅ Canonical Domain + Social Cards + Schema Sync (2026-05-31)

- **Custom domain:** Moved everything to `pct-geoguesser.economicurtis.com` (GoDaddy CNAME -> Cloudflare Pages custom domain). Updated `MISC_BASE_URL`, every `og:url`, and the OAuth `redirectTo`; updated Supabase Auth Site URL + redirect allowlist so post-login lands on the canonical domain.
- **Social preview cards:** Full Open Graph + Twitter card blocks added to every page (landing, game, practice, leaderboard, hiker), pointing at the canonical preview image.
- **Timer:** Bumped 45s -> 60s across both game modes and the landing page. README language kept duration-agnostic so it does not need re-editing on future tweaks.
- **Landing footer:** New "Leaderboard · About" footer links.
- **Schema docs synced to production:** `supabase_schema.sql` updated (NUMERIC scores, score cap -> 2680, session-cap comment -> 15, `site_settings` table + RLS). `supabase_admin_rpcs.sql` documents the `admin_set_setting()` RPC. Documentation only; the live DB was already correct.
- **Repo hygiene:** `.gitignore` now ignores only `deploy/miles/` (637 MB) rather than all of `deploy/`, so generated HTML is version-controlled. `build.sh` header corrected to reflect the manual wrangler deploy (not git-triggered). Deleted the stale `deploy/leaderboard/all-time/` page.

---

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
