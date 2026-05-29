# app-game-v1-testing

The PCT GeoGuesser game — v1 (demo / testing build).

This is the playable game hosted at **https://pct-geoguesser.pages.dev**.  
Players look at a trail photo, guess what PCT mile it was taken at, and score points based on accuracy.

---

## File Structure

```
app-game-v1-testing/
├── README.md        ← this file
├── build.py         ← generates index.html from misc/photos.csv
└── index.html       ← the full game (auto-generated — don't edit directly)
```

The output (`index.html`) is copied to `deploy/` and pushed to Cloudflare Pages.

---

## How to build and deploy

**1. Rebuild the game HTML:**
```bash
python3 app-game-v1-testing/build.py
```

**2. Copy to the deploy folder:**
```bash
cp app-game-v1-testing/index.html deploy/index.html
```

**3. Deploy to Cloudflare Pages:**
```bash
npx wrangler pages deploy "/Volumes/PCT2025-4T/2026 PCT GeoGuesser Game/deploy" --project-name=pct-geoguesser
```

The hash URL it prints (e.g. `https://abc123.pct-geoguesser.pages.dev`) is an immutable  
permalink for that exact build. The main domain (`pct-geoguesser.pages.dev`) updates  
automatically — no extra step needed.

---

## How the game works

1. **Photo selection** — `build.py` reads `misc/photos.csv` and filters to rows with  
   `version = "v1-demo"` (roughly half the photo pool, alternating by mile order).  
   The JS then picks 2 random photos from each of the 5 PCT sections (10 photos total)  
   so every game covers the full trail.

2. **Gameplay loop** — four screens, each a full-height `<div class="screen">`:
   - **Start** — logo, title, rules, "Start Game" button
   - **Guess** — photo, 30-second countdown timer, mile number input + trail slider, hints
   - **Result** — score card (your guess vs true mile, verdict, running total), photo reveal, "Next" button
   - **End** — final score, per-photo results table with lightbox thumbnails, "Play Again" → back to Start

3. **Scoring** — within ±3 miles = perfect (0 pts). Otherwise, score = miles off (rounded).  
   Timed-out rounds score 1,327.5 pts (trail midpoint). Lowest total wins.

4. **Image hosting** — all photos live at `https://pct-geoguesser.pages.dev/miles/{id}.jpeg`  
   (or `.jpg`). The `url` column in `photos.csv` holds the full URL for each photo.

---

## Key design decisions

| Decision | Rationale |
|---|---|
| Single `index.html` | No build tool, no server, no framework — just open the file |
| Photo data baked into JS | No API calls during gameplay; works offline after first load |
| `_preloadCache` map | Prevents the GC from cancelling mid-flight preload requests |
| Futura → Open Sans fallback | Futura is built-in on macOS/iOS; Open Sans loaded from Google Fonts for other platforms |
| `touch-action: none` on photo | Hands all touch events to the JS zoom handler; prevents iOS from intercepting pinch gestures |
| `version = "v1-demo"` split | Reserves the other half of photos (`v2-scored`) for a future logged/scored version |

---

## Trail sections and colours

| Section | Miles | Colour |
|---|---|---|
| Southern California | 0 – 702.1 | `#c8a96e` (tan) |
| The Sierra | 702.1 – 1092.3 | `#d8d8d8` (grey) |
| Northern California | 1092.3 – 1692.0 | `#2ab062` (green) |
| Oregon | 1692.0 – 2147.0 | `#008080` (teal) |
| Washington | 2147.0 – 2655.5 | `#1D502E` (forest green) |

The slider track is a CSS gradient across these colours. The slider thumb dot  
uses a tri-colour gradient that blends toward the neighbouring section colours  
based on how far into the current section the thumb is positioned.

---

## Future: v2

v2 will add user login (to track scores across sessions) and a global leaderboard.  
It will draw from `version = "v2-scored"` photos — a separate pool so v1 and v2  
don't overlap. The app will live in `app-game-v2/` when that work begins.
