# PCT GeoGuesser

A GeoGuesser-style web game for the Pacific Crest Trail.
Players see a trail photo and guess the mile marker. The closer, the better.
Highest score wins — max 2655.8 pts (one point per PCT mile). 

Live at **https://pct-geoguesser.pages.dev**

---

## What Have We Done Here, & Why?

We had a large collection of photos taken during a PCT hike — each
filename encoding the trail mile, direction, and date. The idea: make a game
where hikers can test their trail knowledge photo by photo.

**The raw material:** 245+ trail photos with mile, direction (NoBo/SoBo), section,
and date, and other metadata in each filename.

**The challenge:** Turn that into a playable game without giving away the answer
in URLs or filenames, handle login and a global leaderboard, and make it feel
polished on mobile.

**What we did:**
- Anonymized every photo with a random 5-letter ID so filenames don't reveal location
- Built a practice mode (no login) and a scored mode (Google login, leaderboard)
- Hosted everything as static files on Cloudflare Pages with Supabase as the backend

---

## File structure

```
2026 PCT GeoGuesser Game/
├── README.md                        ← this file
├── TODO.md                          ← progress log (will move to GitHub PRs)
│
├── img/
│   ├── raw-photos-save/             ← original screenshots, never modified
│   │   └── Summer 2025/
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
├── app-game/                        ← both game modes (single source of truth)
│   ├── build.py                     ← generates practice + scored HTML
│   ├── practice/
│   │   └── index.html               ← (auto-generated) practice game at /practice/
│   └── scored/
│       └── index.html               ← (auto-generated) scored game at /game/
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
    ├── miles/                       ← 245+ photos named {id}.jpeg / {id}.png
    └── misc/                        ← logos + social preview image
```

---

## Pages

### `/` — Landing page
Entry point. Links to both game modes and the leaderboard.
Tagline, logo, and "About PCT GeoGuesser" footer link (page TBD).

### `/practice/` — Practice game (v1)
No login required. 10 photos per game — Mile 1 is always first (easy opener),
remaining 9 drawn randomly across all 5 PCT sections. 45-second timer per photo.
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

## Scoring

The scoring system was redesigned after playtesting. The original method added up the raw mile difference between each guess and the correct answer — lowest total wins. It was technically simple, but playtesters found "lower is better" counterintuitive for a game.

The new system borrows from the real GeoGuessr game's scoring formula, adapted with custom parameters for the PCT. Like GeoGuessr, it uses exponential decay: the further off your guess, the faster your score drops. This means wild guesses hurt more than under the old linear method. And now, intuitively, the best guesser now has the **highest** score.

**Formula (per photo):**
```
S = (2655.8 / 10) × e^(−10 × d_eff / 2655.8)

where d_eff = max(0, |guess − actual| − 3)
```

- `d_eff` is the "effective distance" — guesses within **±3 miles** of the correct answer earn full credit
- The constant **2655.8** is the length of the PCT in miles — also the maximum possible total score (one point per mile of trail)

| Miles off | Score per photo | % of max |
|----------:|----------------:|---------:|
| 0 – 3     | 265.6 (perfect) | 100%     |
| 10        | 258.7           |  97%     |
| 50        | 222.5           |  84%     |
| 100       | 184.3           |  69%     |
| 250       | 104.8           |  40%     |
| 500       |  40.9           |  15%     |
| Timeout   |   0.0           |   0%     |

A perfect game (all 10 guesses within 3 miles) scores **2,655.8 pts** — the full length of the trail.

---

## Workflow

### Adding new photos

```
1. Drop photos into img/raw-photos-save/Summer 2025/
           ↓
2. python3 misc/generate_photo_csv.py     →  misc/photos.csv  (preserves existing IDs)
           ↓
3. python3 misc/copy_rename_photos.py     →  deploy/miles/{id}.jpeg  (skips already-done)
```

Or manually: assign an ID, add a row to photos.csv, copy the file to `deploy/miles/`.

### Rebuilding and deploying

```
bash build.sh
          ↓
npx wrangler pages deploy deploy/ --project-name=pct-geoguesser
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
