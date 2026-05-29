# PCT GeoGuesser

A GeoGuesser-style web game for the Pacific Crest Trail.
Players see a trail photo and guess the mile marker. The closer, the better.
Lowest score wins. 

Live at **https://pct-geoguesser.pages.dev**

---

## What we built and why

We had a large collection of photos taken during a PCT hike — each
filename encoding the trail mile, direction, and date. The idea: make a game
where hikers can test their trail knowledge photo by photo.

**The raw material:** ~200+ trail photos with mile, direction (NoBo/SoBo), section,
and date metadata in each filename.

**The challenge:** Turn that into a playable game without giving away the answer
in URLs or filenames, handle login and a global leaderboard, and make it feel
polished on mobile.

**What we did:**
- Anonymized every photo with a random 5-letter ID so filenames don't reveal location
- Built a practice mode (no login) and a scored mode (Google login, leaderboard)
- Hosted everything as static files on Cloudflare Pages with Supabase as the backend

---

## Pages

### `/` — Landing page
Entry point. Links to both game modes and the leaderboard.
Tagline, logo, and "About PCT GeoGuesser" footer link (page TBD).

### `/practice/` — Practice game (v1)
No login required. 10 photos per game — Mile 1 is always first (easy opener),
remaining 9 drawn randomly across all 5 PCT sections. 30-second timer per photo.
Slider to guess, score shown per round and in a final summary table. No data saved.

### `/game/` — Scored game (v2)
Google login required. Same gameplay as practice. Scores are saved to Supabase
via the `submit_game()` RPC. After the game, shows the player's 90-day leaderboard
rank. Profile setup on first login (trail name, PCT year, optional "about" blurb).
Players can edit their profile from the start screen at any time.

### `/leaderboard/` and `/leaderboard/all-time/`
Top players by total score. 90-day view on the main leaderboard, all-time on the
second page. Trail names link to each player's hiker profile. Shows score, perfects,
and games played.

### `/hiker/?id=<uuid>` — Hiker profile
Public profile page for any player. Shows trail name, PCT year, about blurb, stat
chips (games, best score, average score, perfects), and a game history table. Best
game gets a ⭐ badge; if it's within 90 days, a 📊 ranked badge too.

### `/admin/` — Admin dashboard
Only accessible to a select Admin (enforced by Supabase SECURITY DEFINER
RPCs — not just client-side). Three tabs:

- **Recent Games** — last 100 scored games, with player links and timestamps
- **Photo Stats** — per-photo stats: appearances, average guessing error, SD
- **Edit Database** — search players by name; inline trail-name editing; delete a
  player's games only, or delete the full player record

---

## File structure

```
2026 PCT GeoGuesser Game/
├── README.md                        ← this file
├── TODO.md                          ← progress log (will move to GitHub PRs)
│
├── raw-photos-save/
│   └── Summer 2025/                 ← original screenshots, never modified
│
├── img/
│   ├── miles/                       ← photos copied + renamed to their random ID (source)
│   └── misc/                        ← logo and preview images (source files)
│
├── misc/
│   ├── photos.csv                   ← master table: one row per photo
│   ├── supabase_config.py           ← publishable Supabase URL + anon key
│   ├── supabase_schema.sql          ← full schema: tables, RLS, triggers, RPCs
│   ├── supabase_admin_rpcs.sql      ← admin-only RPCs (run once in Supabase SQL editor)
│   ├── generate_photo_csv.py        ← builds photos.csv from raw filenames
│   └── copy_rename_photos.py        ← copies + renames photos into img/miles/
│
├── app-landing/                     ← landing page at /
│   ├── build.py
│   └── index.html                   ← (auto-generated)
│
├── app-game-v1-testing/             ← practice game at /practice/
│   ├── build.py
│   ├── index.html                   ← (auto-generated)
│   └── README.md
│
├── app-game-v2/                     ← scored game at /game/
│   ├── build.py
│   └── index.html                   ← (auto-generated)
│
├── app-leaderboard/                 ← leaderboard pages at /leaderboard/ and /leaderboard/all-time/
│   ├── build.py
│   └── index.html                   ← (auto-generated; both leaderboard pages use one file)
│
├── app-hiker/                       ← hiker profile at /hiker/?id=<uuid>
│   ├── build.py
│   └── index.html                   ← (auto-generated)
│
├── app-admin/                       ← admin dashboard at /admin/
│   ├── build.py
│   └── index.html                   ← (auto-generated)
│
├── app-explore/                     ← local-only photo browser (not deployed)
│   └── ...
│
└── deploy/                          ← what gets pushed to Cloudflare Pages
    ├── index.html                   ← landing page
    ├── practice/index.html          ← v1 practice game
    ├── game/index.html              ← v2 scored game
    ├── leaderboard/index.html       ← 90-day leaderboard
    ├── leaderboard/all-time/index.html ← all-time leaderboard
    ├── hiker/index.html             ← hiker profile (loads player via ?id= query param)
    ├── admin/index.html             ← admin dashboard
    ├── miles/                       ← 202+ photos named {id}.jpeg / {id}.png
    └── misc/                        ← logos + social preview image
```

---

## Workflow

### Adding new photos

```
1. Drop photos into raw-photos-save/Summer 2025/
           ↓
2. python3 misc/generate_photo_csv.py     →  misc/photos.csv  (preserves existing IDs)
           ↓
3. python3 misc/copy_rename_photos.py     →  img/miles/{id}.jpeg  (skips already-done)
           ↓
4. cp img/miles/* deploy/miles/
```

Or manually: assign an ID, add a row to photos.csv, copy the file to deploy/miles/.

### Rebuilding and deploying

```
python3 app-landing/build.py
python3 app-game-v1-testing/build.py
python3 app-game-v2/build.py
python3 app-leaderboard/build.py
python3 app-hiker/build.py
python3 app-admin/build.py
          ↓
cp app-landing/index.html             deploy/index.html
cp app-game-v1-testing/index.html     deploy/practice/index.html
cp app-game-v2/index.html             deploy/game/index.html
cp app-leaderboard/index.html         deploy/leaderboard/index.html
cp app-hiker/index.html               deploy/hiker/index.html
cp app-admin/index.html               deploy/admin/index.html
          ↓
npx wrangler pages deploy "/Volumes/PCT2025-4T/2026 PCT GeoGuesser Game/deploy" \
  --project-name=pct-geoguesser
```

---

## Technical appendix

Everything is static HTML — no server-side rendering, no build toolchain beyond
the Python scripts that generate each `index.html`.

| Technology | Role |
|---|---|
| **Cloudflare Pages** | Static hosting. Serves all HTML, images, and assets. Free tier, global CDN. Deploy via `wrangler pages deploy`. |
| **Supabase** | Backend-as-a-service. Hosts PostgreSQL with Row Level Security, Google OAuth, and server-side RPCs (`submit_game`, admin functions). The publishable anon key is safe to embed in HTML because RLS restricts what it can do. |
| **Google OAuth (via Supabase)** | One-click login for the scored game. No password flow needed. |
| **PostgreSQL (Supabase)** | Four tables: `profiles`, `game_sessions`, `game_guesses`, `photo_stats`. Triggers enforce rate limiting (1 min between games) and a per-user game cap (10). |
| **Welford's online algorithm** | Used in `submit_game()` to maintain running mean, variance, and SD for photo stats without storing raw guesses. Numerically stable, requires only three stored values (n, mean, M2). |
| **SECURITY DEFINER RPCs** | `submit_game()` and all admin RPCs run with table-owner privileges, bypassing RLS to write to tables that are otherwise read-only to clients. Admin RPCs verify the caller's email server-side — safe to call via the anon key. |
| **Python (build scripts)** | Each app's `build.py` bakes the relevant slice of `photos.csv` into a self-contained `index.html` as an inline JSON array. No API call needed for photo metadata at runtime. |
| **Vanilla JS** | All game logic, UI, and Supabase client calls. No framework. The Supabase JS client (`@supabase/supabase-js` via CDN) handles auth and database queries. |
| **CSS custom properties** | Theming (dark UI, PCT section colours, teal accent). The trail slider thumb uses a tri-colour gradient computed from the guess position — rendered entirely in CSS via `--thumb-left`, `--thumb-center`, `--thumb-right` variables set by JS. |
| **Wrangler CLI** | Cloudflare's CLI tool. Used only for `pages deploy` — no Workers, no edge functions. |
