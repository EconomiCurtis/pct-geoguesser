# ──────────────────────────────────────────────────────────────────────────────
# build.py  —  PCT GeoGuesser  (game v1)
#
# Reads misc/photos.csv and generates a single self-contained index.html that
# is the full GeoGuesser game.  All HTML, CSS, and JS live in this one file;
# the only external dependencies are:
#   • Google Fonts (Open Sans) — loaded at runtime from fonts.googleapis.com
#   • Images served from Cloudflare Pages at MISC_BASE_URL and /miles/{id}.ext
#
# To rebuild after editing:
#   python3 app-game-v1-testing/build.py
#
# To deploy:
#   cp app-landing/index.html          deploy/index.html
#   cp app-game-v1-testing/index.html  deploy/practice/index.html
#   npx wrangler pages deploy deploy/ --project-name=pct-geoguesser
#
# See app-game-v1-testing/README.md for full documentation.
# ──────────────────────────────────────────────────────────────────────────────

import csv
import json
import os

HERE     = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "..", "misc", "photos.csv")
OUT_PATH = os.path.join(HERE, "index.html")
MISC_BASE_URL = "https://pct-geoguesser.pages.dev/misc"  # logos & other static assets

with open(CSV_PATH) as f:
    rows = list(csv.DictReader(f))

v1_photos = [r for r in rows if r.get("version") == "v1-demo"]

game_data = json.dumps(
    [
        {
            "id": r["id"],
            "mile": r["mile"],
            "direction": r["direction"],
            "section": r["section"],
            "date": r["date"],
            "url": r["url"],
        }
        for r in v1_photos
    ]
)

# ── Trail slider: section colours + generated HTML ────────────
_TRAIL_MAX = 2655.5
_SECTIONS = [
    {
        "abbr": "S. California",
        "start": 0.0,
        "end": 702.1,
        "color": "#c8a96e",
        "tcol": "#d4b07a",
        "bg": "rgba(200,169,110,.2)",
    },
    {
        "abbr": "Sierra",
        "start": 702.1,
        "end": 1092.3,
        "color": "#d8d8d8",
        "tcol": "#e8e8e8",
        "bg": "rgba(240,246,252,.12)",
    },
    {
        "abbr": "N. California",
        "start": 1092.3,
        "end": 1692.0,
        "color": "#2ab062",
        "tcol": "#4fca84",
        "bg": "rgba(42,176,98,.2)",
    },
    {
        "abbr": "Oregon",
        "start": 1692.0,
        "end": 2147.0,
        "color": "#008080",
        "tcol": "#5fd4d4",
        "bg": "rgba(0,128,128,.2)",
    },
    {
        "abbr": "Washington",
        "start": 2147.0,
        "end": 2655.5,
        "color": "#1D502E",
        "tcol": "#7ecb96",
        "bg": "rgba(29,80,46,.3)",
    },
]


def _mpct(m):
    return f"{m / _TRAIL_MAX * 100:.2f}%"


# Gradient for the slider track
_grad = ", ".join(
    f"{s['color']} {_mpct(s['start'])} {_mpct(s['end'])}" for s in _SECTIONS
)
slider_gradient = f"linear-gradient(to right, {_grad})"

# Boundary mile labels (positioned absolutely over the track)
_bounds = [s["start"] for s in _SECTIONS] + [_TRAIL_MAX]
_marks = []
for _i, _m in enumerate(_bounds):
    _label = f"{int(_m):,}"
    if _i == 0:
        _style = "left:0;transform:none"
    elif _i == len(_bounds) - 1:
        _style = "right:0;left:auto;transform:none"
    else:
        _style = f"left:{_mpct(_m)};transform:translateX(-50%)"
    _marks.append(f'<span style="{_style}">{_label}</span>')
slider_marks = "\n      ".join(_marks)

# Section name bars (proportional flex widths)
_sec_bars = []
for _s in _SECTIONS:
    _miles = _s["end"] - _s["start"]
    _sec_bars.append(
        f'<div class="ts-sec" style="flex:{_miles:.1f};'
        f'background:{_s["bg"]};color:{_s["tcol"]}">{_s["abbr"]}</div>'
    )
slider_sections = "\n      ".join(_sec_bars)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>PCT GeoGuesser</title>
<!-- Open Graph / social preview -->
<meta property="og:type"        content="website">
<meta property="og:url"         content="https://pct-geoguesser.pages.dev/">
<meta property="og:title"       content="PCT GeoGuesser">
<meta property="og:description" content="How well do you know the PCT?">
<meta property="og:image"       content="{MISC_BASE_URL}/preview.png">
<meta name="twitter:card"        content="summary_large_image">
<meta name="twitter:title"       content="PCT GeoGuesser">
<meta name="twitter:description" content="How well do you know the PCT?">
<meta name="twitter:image"       content="{MISC_BASE_URL}/preview.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="icon" type="image/png" href="{MISC_BASE_URL}/pct-geoguesser-favicon.png">
<link rel="apple-touch-icon" href="{MISC_BASE_URL}/pct-geoguesser-favicon.png">
<meta name="theme-color" content="#0d1117">
<meta name="description" content="How well do you know the Pacific Crest Trail? Guess the trail mile from 10 photos.">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  /* Dark shell */
  --bg:        #0d1117;
  --surface:   #161b22;
  --surface2:  #21262d;
  --border:    #30363d;
  --text:      #f0f6fc;
  --muted:     #8b949e;

  /* PCT palette */
  --pct-green: #1D502E;   /* forest green  — buttons, accents */
  --pct-teal:  #008080;   /* teal/dark cyan — victory, NoBo   */
  --pct-blue:  #1C2D50;   /* deep navy     — SoBo, backup     */
  --pct-white: #FFFFFF;

  /* Functional */
  --timer-red: #dc2626;
  --perfect:   #008080;
  --nobo-col:  #2ab062;   /* NorCal green — NoBo heading north through forests */
  --sobo-col:  #c8a96e;   /* SoCal tan    — SoBo heading south toward desert   */
  --north-col: #6fd4a0;   /* light green for "N miles North" verdict text      */
  --south-col: #c8a96e;   /* sandy tan for "N miles South" verdict text        */
}}

body {{
  font-family: 'Futura', 'Futura PT', 'Open Sans', Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}

/* ── Screens ─────────────────────────────────────────────── */
.screen {{ display: none; flex-direction: column; height: 100dvh; overflow: hidden; }}
.screen.active {{ display: flex; }}

/* ── Shared buttons ──────────────────────────────────────── */
.btn-green {{
  background: var(--pct-green); color: var(--pct-white);
  border: none; border-radius: 10px;
  padding: 13px 36px; font-size: 16px; font-weight: 700;
  cursor: pointer; transition: filter .15s, transform .1s;
  letter-spacing: .01em;
}}
.btn-green:hover {{ filter: brightness(1.25); transform: translateY(-1px); }}
.btn-green:active {{ transform: translateY(0); }}

.btn-outline {{
  background: transparent; color: var(--text);
  border: 1px solid var(--border); border-radius: 10px;
  padding: 13px; font-size: 15px; font-weight: 600;
  cursor: pointer; width: 100%; transition: background .15s, border-color .15s;
}}
.btn-outline:hover {{ background: var(--surface2); border-color: var(--muted); }}

/* ══════════════════════════════════════════════════════════
   START SCREEN
══════════════════════════════════════════════════════════ */
#screen-start {{
  align-items: center; justify-content: center;
  padding: 24px 20px; gap: 18px; text-align: center; overflow-y: auto;
}}

.logo-pair {{
  display: flex; align-items: center; justify-content: center;
}}
.logo-box {{
  background: #fff;
  border-radius: 10px;
  border: 3px solid #000;
  box-shadow: 0 0 0 3px #fff;
  padding: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}}
.logo-pair img {{ object-fit: contain; }}
.logo-old {{ height: 94px;  width: auto; }}
.logo-new {{ height: 84px;  width: auto; }}

#screen-start h1 {{
  font-size: clamp(26px, 6vw, 46px);
  font-weight: 800; line-height: 1.1;
  color: var(--pct-white);
  text-shadow: 0 0 30px rgba(0,128,128,.4);
}}
#screen-start h1 span {{ color: var(--pct-teal); }}

.start-sub {{
  color: var(--muted); font-size: 14px; max-width: 360px; line-height: 1.5;
}}

.rules-card {{
  background: var(--surface);
  border: 1px solid var(--pct-green);
  border-radius: 12px; padding: 16px 18px;
  max-width: 400px; width: 100%; text-align: left;
}}
.rules-card h3 {{
  font-size: 10px; text-transform: uppercase;
  letter-spacing: .12em; color: var(--pct-teal); margin-bottom: 10px;
}}
/* Space before 2nd and 3rd section headings */
.rules-card ul + h3 {{ margin-top: 14px; }}
.rules-card ul {{ list-style: none; display: flex; flex-direction: column; gap: 8px; }}
.rules-card li {{
  display: flex; align-items: baseline; gap: 9px;
  font-size: 13px; line-height: 1.45; color: var(--text);
}}
.rules-card li::before {{ content: '▸'; color: var(--pct-green); flex-shrink: 0; }}
.rules-card a {{ color: var(--pct-teal); text-decoration: underline; }}
.rules-card a:hover {{ color: #5fd4d4; }}

/* Small grey text below the card — will become a link later */
.about-link {{ font-size: 12px; color: var(--muted); text-align: center; }}

/* ── Start screen: larger logos on mobile, uniform padding ── */
@media (max-width: 640px) {{
  .logo-box {{ padding: 18px; gap: 24px; }}
  .logo-old {{ height: 140px; }}
  .logo-new {{ height: 126px; }}
}}

/* ── Start screen: desktop scale-up ───────────────────── */
@media (min-width: 900px) {{
  #screen-start {{ gap: 26px; }}
  .logo-old {{ height: 117px; }}
  .logo-new {{ height: 106px; }}
  #screen-start h1 {{ font-size: clamp(52px, 5.5vw, 88px); }}
  .start-sub {{ font-size: 18px; max-width: 520px; }}
  .rules-card {{ max-width: 580px; padding: 22px 26px; }}
  .rules-card h3 {{ font-size: 12px; margin-bottom: 14px; }}
  .rules-card li {{ font-size: 16px; }}
  .btn-green {{ font-size: 18px; padding: 15px 44px; }}
}}

/* ══════════════════════════════════════════════════════════
   GUESS SCREEN
══════════════════════════════════════════════════════════ */
.topbar {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 14px; background: var(--surface);
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}}
.progress-text {{ font-size: 13px; font-weight: 600; color: var(--muted); }}
.progress-text strong {{ color: var(--text); }}

/* Full-width red timer bar directly below topbar */
.timer-bar-track {{
  width: 100%; height: 7px; background: var(--surface2); flex-shrink: 0;
}}
.timer-bar-fill {{
  height: 100%; background: var(--timer-red);
  transition: width .95s linear;
}}

/* Countdown number in topbar — bold, red */
.timer-num {{
  font-size: 20px; font-weight: 800; color: var(--timer-red);
  font-variant-numeric: tabular-nums; min-width: 32px; text-align: right;
}}

/* Photo */
.photo-frame {{
  flex: 1; min-height: 0; position: relative;
  display: flex; align-items: center; justify-content: center;
  background: #000; overflow: hidden;
  touch-action: none; /* JS handles all touch events for pinch-to-zoom */
}}
.photo-frame img {{
  max-width: 100%; max-height: 100%; object-fit: contain; display: block;
  transform-origin: center center; will-change: transform;
}}

/* Hint strip — sits below photo, above input */
.hint-strip {{
  display: flex; justify-content: center; align-items: center; gap: 12px;
  padding: 9px 14px; background: var(--surface);
  border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}}
.hint-chip {{
  display: flex; align-items: center; gap: 6px;
  border-radius: 6px; padding: 5px 13px;
  font-size: 13px; font-weight: 700; letter-spacing: .02em;
  border: 1px solid transparent;
}}
.hint-season {{
  background: rgba(29,80,46,.25); color: #7ecb96;
  border-color: var(--pct-green);
}}
.hint-nobo {{
  background: rgba(42,176,98,.18); color: #6fd4a0;
  border-color: var(--nobo-col);
}}
.hint-sobo {{
  background: rgba(200,169,110,.18); color: var(--sobo-col);
  border-color: var(--sobo-col);
}}

/* Input section */
.input-section {{
  flex-shrink: 0; background: var(--surface);
  padding: 12px 14px; display: flex; flex-direction: column; gap: 8px;
}}
.input-label {{
  font-size: 11px; color: var(--muted); text-align: center;
  text-transform: uppercase; letter-spacing: .09em;
}}
.input-row {{ display: flex; gap: 9px; }}

#mile-input {{
  flex: 1; background: var(--surface2); color: var(--text);
  border: 2px solid var(--border); border-radius: 8px;
  padding: 10px 12px; font-size: 26px; font-weight: 700;
  text-align: center; outline: none; -moz-appearance: textfield;
}}
#mile-input::-webkit-outer-spin-button,
#mile-input::-webkit-inner-spin-button {{ -webkit-appearance: none; }}
#mile-input:focus {{ border-color: var(--pct-teal); }}
#mile-input::placeholder {{ color: var(--border); font-size: 18px; font-weight: 400; }}

.btn-submit {{
  background: var(--pct-green); color: var(--pct-white);
  border: none; border-radius: 8px;
  padding: 10px 18px; font-size: 14px; font-weight: 700;
  cursor: pointer; white-space: nowrap; transition: filter .15s;
}}
.btn-submit:hover {{ filter: brightness(1.3); }}

/* Trail section slider */
.trail-slider-wrap {{
  display: flex; flex-direction: column; gap: 4px; padding-top: 2px;
}}
#trail-slider {{
  -webkit-appearance: none; appearance: none;
  width: 100%; height: 6px; border-radius: 3px;
  background: {slider_gradient};
  outline: none; cursor: pointer;
  /* Thumb colours: updated by JS as the slider moves.
     Three stops: left edge blends toward previous section,
     center = current section, right edge blends toward next section. */
  --thumb-left:   #d4b07a;
  --thumb-center: #c8a96e;
  --thumb-right:  #c8a96e;
  --thumb-glow:   rgba(200,169,110,.35);
}}
#trail-slider::-webkit-slider-thumb {{
  -webkit-appearance: none;
  width: 22px; height: 22px;
  background: linear-gradient(90deg, var(--thumb-left) 0%, var(--thumb-center) 50%, var(--thumb-right) 100%);
  border-radius: 50%; border: 2px solid rgba(255,255,255,.2);
  cursor: grab;
  box-shadow: 0 2px 6px rgba(0,0,0,.7), 0 0 0 3px var(--thumb-glow);
}}
#trail-slider::-moz-range-thumb {{
  width: 22px; height: 22px;
  background: linear-gradient(90deg, var(--thumb-left) 0%, var(--thumb-center) 50%, var(--thumb-right) 100%);
  border-radius: 50%; border: 2px solid rgba(255,255,255,.2);
  cursor: grab; box-shadow: 0 2px 6px rgba(0,0,0,.7);
}}
.trail-marks {{
  position: relative; height: 14px;
}}
.trail-marks span {{
  position: absolute; font-size: 9px; color: var(--muted);
  font-variant-numeric: tabular-nums; line-height: 1; white-space: nowrap;
}}
.trail-sections {{
  display: flex; width: 100%; gap: 1px; border-radius: 3px; overflow: hidden;
}}
.ts-sec {{
  text-align: center; font-size: 9px; font-weight: 600;
  padding: 2px 1px; overflow: hidden; white-space: nowrap;
  letter-spacing: .02em;
}}

/* ── Larger slider thumb on touch screens ──────────────── */
@media (pointer: coarse) {{
  #trail-slider {{ height: 8px; }}
  #trail-slider::-webkit-slider-thumb {{ width: 32px; height: 32px; }}
  #trail-slider::-moz-range-thumb    {{ width: 32px; height: 32px; }}
}}

/* ══════════════════════════════════════════════════════════
   RESULT SCREEN
══════════════════════════════════════════════════════════ */
#screen-result {{ overflow-y: auto; }}

/* Score card — sits above photo, centered/compact */
.result-score-wrap {{
  flex-shrink: 0; display: flex; justify-content: center;
  padding: 12px 16px 0;
}}
.result-score-card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px 20px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  width: 100%; max-width: 420px;
}}

/* Two columns: Your Guess | True Mile */
.rsc-cols {{
  display: flex; align-items: flex-start;
  justify-content: center; width: 100%;
}}
.rsc-col {{
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px;
}}
.rsc-divider {{
  width: 1px; background: var(--border); align-self: stretch; margin: 0 16px;
}}
.rsc-label {{
  font-size: 10px; text-transform: uppercase;
  letter-spacing: .09em; color: var(--muted);
}}
.rsc-num {{
  font-size: 26px; font-weight: 800;
  font-variant-numeric: tabular-nums; color: var(--text);
}}
.rsc-num.true-mile {{ color: var(--pct-teal); }}

/* Small "Your Guess Was" eyebrow above verdict */
.rsc-guess-was {{
  font-size: 9px; text-transform: uppercase;
  letter-spacing: .1em; color: var(--muted); margin-bottom: -4px;
}}

/* Verdict — same visual weight as the numbers */
.rsc-verdict {{
  font-size: 22px; font-weight: 800; text-align: center; line-height: 1.2;
}}
.rsc-verdict.spoton  {{ color: var(--perfect); }}
.rsc-verdict.north   {{ color: var(--north-col); }}
.rsc-verdict.south   {{ color: var(--south-col); }}
.rsc-verdict.timeout {{ color: var(--muted); font-size: 16px; font-weight: 600; }}

/* Round + Total rows */
.rsc-scores {{
  width: 100%; display: flex; flex-direction: column; gap: 4px;
  border-top: 1px solid var(--border); padding-top: 8px;
}}
.rsc-score-row {{
  display: flex; justify-content: space-between; align-items: baseline;
}}
.rsc-score-label {{
  font-size: 11px; color: var(--muted);
  text-transform: uppercase; letter-spacing: .08em;
}}
.rsc-score-val {{
  font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums;
}}
.rsc-score-val.perfect {{ color: var(--perfect); }}

/* Photo — below score card */
.result-photo-wrap {{
  flex: 1; min-height: 180px; max-height: 50vh; position: relative;
  display: flex; align-items: center; justify-content: center;
  background: #000; overflow: hidden; margin-top: 10px;
  touch-action: none; /* JS handles pinch-to-zoom */
}}
.result-photo-wrap img {{
  width: 100%; height: 100%; object-fit: contain; display: block;
  transform-origin: center center; will-change: transform;
}}

/* Small metadata chips below photo */
.answer-meta-bar {{
  flex-shrink: 0; display: flex; flex-wrap: wrap;
  justify-content: center; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: var(--surface); border-bottom: 1px solid var(--border);
}}
.a-chip {{
  font-size: 11px; font-weight: 600; padding: 3px 10px;
  border-radius: 20px; background: var(--surface2); color: var(--muted);
  border: 1px solid var(--border);
}}
.a-chip.mile {{
  color: var(--pct-teal); border-color: var(--pct-teal);
  background: rgba(0,128,128,.12); font-size: 13px; font-weight: 700;
}}

/* Next button wrapper */
.result-actions {{
  flex-shrink: 0; padding: 12px 14px;
  background: var(--surface); border-top: 1px solid var(--border);
}}

/* ══════════════════════════════════════════════════════════
   END SCREEN
══════════════════════════════════════════════════════════ */
#screen-end {{
  overflow-y: auto; padding: 20px 14px 32px;
  align-items: center; gap: 18px;
}}
.end-title {{
  font-size: clamp(22px, 5vw, 34px); font-weight: 800; text-align: center;
}}
.final-box {{
  background: var(--surface); border: 1px solid var(--pct-teal);
  border-radius: 14px; padding: 18px 28px; text-align: center;
  width: 100%; max-width: 300px;
}}
.final-box .fb-label {{
  font-size: 10px; text-transform: uppercase;
  letter-spacing: .12em; color: var(--muted); margin-bottom: 5px;
}}
.final-box .fb-score {{
  font-size: 52px; font-weight: 800; line-height: 1;
  color: var(--pct-teal); font-variant-numeric: tabular-nums;
}}
.final-box .fb-unit {{ font-size: 12px; color: var(--muted); margin-top: 3px; }}
.final-avg {{
  font-size: 16px; font-weight: 600; color: var(--muted); text-align: center;
  margin-top: -8px;
}}

/* Results table */
.end-table-wrap {{ width: 100%; max-width: 580px; overflow-x: auto; }}
.end-table {{
  width: 100%; border-collapse: collapse; font-size: 13px;
}}
.end-table th {{
  padding: 6px 10px; font-size: 10px; text-transform: uppercase;
  letter-spacing: .09em; border-bottom: 1px solid var(--border);
  white-space: nowrap; font-weight: 700;
}}
.end-table th.th-photo  {{ text-align: left; color: var(--muted); }}
.end-table th.th-guess  {{ text-align: right; color: var(--sobo-col); }}
.end-table th.th-mile   {{ text-align: right; color: var(--pct-teal); }}
.end-table th.th-score  {{ text-align: right; color: #7ecb96; }}

.end-table td {{
  padding: 6px 10px; border-bottom: 1px solid var(--border); vertical-align: middle;
}}
.end-table tr:last-child td {{ border-bottom: none; }}

.end-table .td-thumb {{
  width: 52px; padding: 4px 10px 4px 0;
}}
.et-thumb {{
  width: 52px; height: 38px; object-fit: cover; border-radius: 4px;
  cursor: pointer; display: block; transition: opacity .15s;
  border: 1px solid var(--border);
}}
.et-thumb:hover {{ opacity: .8; border-color: var(--pct-teal); }}

.end-table .td-guess {{
  text-align: right; font-weight: 700; color: var(--sobo-col);
  font-variant-numeric: tabular-nums;
}}
.end-table .td-guess.no-answer {{ color: var(--muted); font-weight: 400; font-size: 11px; }}
.end-table .td-mile  {{
  text-align: right; font-weight: 700; color: var(--pct-teal);
  font-variant-numeric: tabular-nums;
}}
.end-table .td-score {{
  text-align: right; font-weight: 700; font-variant-numeric: tabular-nums;
}}
.end-table .td-score.perfect {{ color: var(--pct-teal); }}
.end-table .td-score.off     {{ color: var(--muted); }}

/* ── Lightbox ─────────────────────────────────────────── */
#lightbox {{
  display: none; position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,.92); align-items: center; justify-content: center;
  flex-direction: column; gap: 12px; padding: 16px;
}}
#lightbox.open {{ display: flex; }}
#lightbox img {{
  max-width: 100%; max-height: 80vh; object-fit: contain; border-radius: 6px;
}}
.lightbox-caption {{
  font-size: 13px; color: var(--muted); text-align: center;
}}
.lightbox-close {{
  position: absolute; top: 14px; right: 14px;
  background: var(--surface2); color: var(--text);
  border: 1px solid var(--border); border-radius: 50%;
  width: 36px; height: 36px; font-size: 18px; line-height: 36px;
  text-align: center; cursor: pointer; transition: background .15s;
}}
.lightbox-close:hover {{ background: var(--border); }}
</style>
</head>
<body>

<!-- ════════════════ START ════════════════ -->
<div id="screen-start" class="screen">
  <div class="logo-pair">
    <div class="logo-box">
      <img src="{MISC_BASE_URL}/pct-orig-logo.webp" class="logo-old" alt="PCT original logo">
      <img src="{MISC_BASE_URL}/pct-new-logo.webp"  class="logo-new" alt="PCT shield logo">
    </div>
  </div>
  <h1>PCT <span>GeoGuesser</span></h1>
  <p class="start-sub">How well do you know the Pacific Crest Trail?</p>
  <div class="rules-card">
    <h3>How to Play</h3>
    <ul>
      <li>You'll see 10 photos taken somewhere along the PCT</li>
      <li><span>Enter the PCT (NoBo) mile you think matches the location (<a href="https://pcta.maps.arcgis.com/apps/instant/sidebar/index.html?appid=3b1817932adf42009f30b6b38828212e" target="_blank" rel="noopener">see PCTA mile markers</a>)</span></li>
      <li>You'll have <strong>30 seconds</strong> to guess</li>
    </ul>
    <h3>Scoring (lower is better)</h3>
    <ul>
      <li>Your score is how many miles off your guesses are</li>
      <li>Within 3 miles = perfect score for that photo (0 points)</li>
      <li><strong>Lowest total score wins</strong></li>
    </ul>
    <h3>Tips</h3>
    <ul>
      <li>Photos can come from anywhere along the 2,655-mile trail.</li>
      <li>Pay attention to the date &amp; hiking direction. Not every photo was taken during summer.</li>
    </ul>
  </div>
  <button class="btn-green" onclick="startGame()">Start Game →</button>
  <p class="about-link">About PCT GeoGuesser</p>
</div>

<!-- ════════════════ GUESS ════════════════ -->
<div id="screen-guess" class="screen">
  <div class="topbar">
    <div class="progress-text">Photo <strong id="g-cur">1</strong> / <strong id="g-tot">10</strong></div>
    <div class="timer-num" id="timer-num">30</div>
  </div>
  <div class="timer-bar-track">
    <div class="timer-bar-fill" id="timer-fill" style="width:100%"></div>
  </div>

  <div class="photo-frame">
    <img id="g-photo" src="" alt="Trail photo">
  </div>

  <!-- Hints in a dedicated strip below photo -->
  <div class="hint-strip">
    <div class="hint-chip hint-season" id="g-season"></div>
    <div class="hint-chip" id="g-direction"></div>
  </div>

  <div class="input-section">
    <div class="input-label">What Mile is this?</div>
    <div class="input-row">
      <input type="number" id="mile-input" min="0" max="2655"
             placeholder="e.g. 1054" autocomplete="off" inputmode="numeric">
      <button class="btn-submit" onclick="submitGuess()">Submit →</button>
    </div>
    <!-- Trail section slider -->
    <div class="trail-slider-wrap">
      <input type="range" id="trail-slider" min="0" max="2655" step="1" value="0">
      <div class="trail-marks">
      {slider_marks}
      </div>
      <div class="trail-sections">
      {slider_sections}
      </div>
    </div>
  </div>
</div>

<!-- ════════════════ RESULT ════════════════ -->
<div id="screen-result" class="screen">

  <!-- Score card above photo -->
  <div class="result-score-wrap">
    <div class="result-score-card">
      <!-- Your Guess | True Mile -->
      <div class="rsc-cols">
        <div class="rsc-col">
          <div class="rsc-label">Your Guess</div>
          <div class="rsc-num" id="r-your-guess"></div>
        </div>
        <div class="rsc-divider"></div>
        <div class="rsc-col">
          <div class="rsc-label">Correct Mile</div>
          <div class="rsc-num true-mile" id="r-true-mile"></div>
        </div>
      </div>
      <!-- Verdict -->
      <div class="rsc-guess-was">Your Guess Was</div>
      <div class="rsc-verdict" id="st-verdict"></div>
      <!-- Round + Total -->
      <div class="rsc-scores">
        <div class="rsc-score-row">
          <span class="rsc-score-label">Round score</span>
          <span class="rsc-score-val" id="st-round"></span>
        </div>
        <div class="rsc-score-row">
          <span class="rsc-score-label">Total score</span>
          <span class="rsc-score-val" id="st-total"></span>
        </div>
      </div>
    </div>
  </div>

  <!-- Photo -->
  <div class="result-photo-wrap">
    <img id="r-photo" src="" alt="">
  </div>

  <!-- Metadata chips -->
  <div class="answer-meta-bar">
    <span class="a-chip mile" id="r-mile"></span>
    <span class="a-chip" id="r-section"></span>
    <span class="a-chip" id="r-date"></span>
    <span class="a-chip" id="r-dir"></span>
  </div>

  <!-- Next button -->
  <div class="result-actions">
    <button class="btn-outline" id="btn-next" onclick="nextPhoto()">Next Photo →</button>
  </div>
</div>

<!-- ════════════════ END ════════════════ -->
<div id="screen-end" class="screen">
  <div class="end-title">Game Complete! 🏁</div>
  <div class="final-box">
    <div class="fb-label">Final Score</div>
    <div class="fb-score" id="final-score"></div>
    <div class="fb-unit">total miles off · lower is better · 0 = perfect</div>
  </div>
  <div class="final-avg" id="final-avg"></div>

  <div class="end-table-wrap">
    <table class="end-table">
      <thead>
        <tr>
          <th class="th-photo">Photo</th>
          <th class="th-mile">Correct Mile</th>
          <th class="th-guess">Your Guess</th>
          <th class="th-score">Score</th>
        </tr>
      </thead>
      <tbody id="end-tbody"></tbody>
    </table>
  </div>

  <button class="btn-green" onclick="window.location.href='/'">Play Again</button>
</div>

<!-- ════════════════ LIGHTBOX ════════════════ -->
<div id="lightbox">
  <div class="lightbox-close" onclick="closeLightbox()">✕</div>
  <img id="lb-img" src="" alt="">
  <div class="lightbox-caption" id="lb-caption"></div>
</div>

<script>
const photos = {game_data};

// ── Config ───────────────────────────────────────────────
const TIMER_SEC          = 30;
const FULL_CREDIT        = 3;       // ±3 miles = perfect (0 pts)
const GAME_SIZE          = 10;
const NO_ANSWER_PENALTY  = 1327.5;  // midpoint of trail

// ── State ────────────────────────────────────────────────
let gamePhotos = [], currentIdx = 0;
let scores = [], guesses = [];
let timerHandle = null, timeLeft = TIMER_SEC;

// ── Image preloading ──────────────────────────────────────
// Keep Image objects in a map so the GC can't discard them mid-download.
// Without this, `(new Image()).src = url` can be collected before the
// request finishes, silently cancelling the preload.
const _preloadCache = {{}};
function preload(url) {{
  if (!_preloadCache[url]) {{
    const img = new Image();
    img.src = url;
    _preloadCache[url] = img;
  }}
}}

// Pre-select + preload an entire game's worth of photos.
// Called on page load (so photos cache while user reads the start screen)
// and again when the end screen is shown (so next game is ready instantly).
function prepareNextGame() {{
  gamePhotos = selectGamePhotos();
  gamePhotos.forEach(p => preload(p.url));
}}

// ── Slider thumb: tri-colour gradient dot ────────────────────
// The dot uses a horizontal 3-stop gradient (left → center → right).
// • center = always the current section's colour
// • left   = lerp(prev-section-color, current, t)  — blends away from
//             the previous section as you move deeper into this one
// • right  = lerp(next-section-color, current, 1-t) — blends toward
//             the next section as you approach the boundary
// t = fraction through the current section (0 = just entered, 1 = about to leave)
const _SECTION_COLORS = [
  {{ start:    0,   end:  702.1, rgb: [200,169,110] }},  // SoCal tan
  {{ start:  702.1, end: 1092.3, rgb: [216,216,216] }},  // Sierra grey
  {{ start: 1092.3, end: 1692.0, rgb: [ 42,176, 98] }},  // NorCal green
  {{ start: 1692.0, end: 2147.0, rgb: [  0,128,128] }},  // Oregon teal
  {{ start: 2147.0, end: 2655.5, rgb: [ 29, 80, 46] }},  // Washington green
];

function _lerp(c0, c1, t) {{
  return c0.map((v, i) => Math.round(v + (c1[i] - v) * t));
}}
function _rgb(c) {{ return `rgb(${{c[0]}},${{c[1]}},${{c[2]}})`; }}

function updateThumbColors(mile) {{
  // Find current section
  let si = 0;
  while (si < _SECTION_COLORS.length - 1 && mile >= _SECTION_COLORS[si + 1].start) si++;
  const sec = _SECTION_COLORS[si];

  // 0 = just entered this section from the left, 1 = about to cross into the next
  const t = (mile - sec.start) / (sec.end - sec.start);

  const center       = sec.rgb;
  const leftNeighbor  = si > 0                            ? _SECTION_COLORS[si - 1].rgb : center;
  const rightNeighbor = si < _SECTION_COLORS.length - 1  ? _SECTION_COLORS[si + 1].rgb : center;

  // left edge:  neighbor colour at entry → center colour at exit
  const leftEdge  = _lerp(leftNeighbor,  center, t);
  // right edge: neighbor colour at exit  → center colour at entry
  const rightEdge = _lerp(rightNeighbor, center, 1 - t);

  const sl = document.getElementById('trail-slider');
  sl.style.setProperty('--thumb-left',   _rgb(leftEdge));
  sl.style.setProperty('--thumb-center', _rgb(center));
  sl.style.setProperty('--thumb-right',  _rgb(rightEdge));
  sl.style.setProperty('--thumb-glow', `rgba(${{center[0]}},${{center[1]}},${{center[2]}},.4)`);
}}

// ── Screens ───────────────────────────────────────────────
function showScreen(id) {{
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}}

// ── Photo selection: Mile 1 always first, then 9 random by section ──
// The opening photo is always Mile 1 — an easy, fun teaching moment.
// The remaining 9 cover all 5 PCT sections (1 more SoCal + 2 each other).
const _FIXED_FIRST_ID = 'tdlce';  // Mile 1 SoBo — always the opener
const _PCT_SECTIONS = [
  'Southern California', 'The Sierra',
  'Northern California', 'Oregon', 'Washington',
];

function selectGamePhotos() {{
  // Fixed opener: Mile 1
  const firstPhoto = photos.find(p => p.id === _FIXED_FIRST_ID);

  // Remaining pool: exclude the fixed first photo
  const rest = photos.filter(p => p.id !== _FIXED_FIRST_ID);

  // 1 more from SoCal + 2 from each other section = 9 more photos
  const perSection = {{
    'Southern California': 1,
    'The Sierra': 2, 'Northern California': 2, 'Oregon': 2, 'Washington': 2,
  }};
  const selected = [];
  for (const sec of _PCT_SECTIONS) {{
    const pool = rest.filter(p => p.section === sec).sort(() => Math.random() - .5);
    selected.push(...pool.slice(0, Math.min(perSection[sec], pool.length)));
  }}

  // Mile 1 first, rest in random order
  return [firstPhoto, ...selected.sort(() => Math.random() - .5)];
}}

// ── Scoring ───────────────────────────────────────────────
function calcScore(guess, trueMile) {{
  return Math.abs(guess - trueMile) <= FULL_CREDIT ? 0 : Math.round(Math.abs(guess - trueMile));
}}

function getVerdictInfo(guess, trueMile) {{
  const diff = guess - trueMile;   // positive = north (higher mile #)
  if (Math.abs(diff) <= FULL_CREDIT) return {{ text: 'Spot On! 🎯',                   cls: 'spoton' }};
  if (diff > 0)                      return {{ text: `${{fmt(diff)}} Miles North`,      cls: 'north'  }};
  return                                    {{ text: `${{fmt(Math.abs(diff))}} Miles South`, cls: 'south'  }};
}}

function fmt(n) {{ return Math.round(n).toLocaleString(); }}

// ── Timer ─────────────────────────────────────────────────
function stopTimer() {{
  if (timerHandle) {{ clearInterval(timerHandle); timerHandle = null; }}
}}

function startTimer() {{
  timeLeft = TIMER_SEC;
  renderTimer();
  timerHandle = setInterval(() => {{
    timeLeft--;
    renderTimer();
    if (timeLeft <= 0) {{
      stopTimer();
      const raw = document.getElementById('mile-input').value.trim();
      raw ? processGuess(parseFloat(raw), false) : processGuess(null, true);
    }}
  }}, 1000);
}}

function renderTimer() {{
  document.getElementById('timer-fill').style.width = (timeLeft / TIMER_SEC * 100) + '%';
  document.getElementById('timer-num').textContent  = timeLeft;
}}

// ── Game flow ─────────────────────────────────────────────
function startGame() {{
  // gamePhotos was pre-selected by prepareNextGame() — already in cache
  currentIdx = 0; scores = []; guesses = [];
  showGuessScreen();
}}

function showGuessScreen() {{
  const p = gamePhotos[currentIdx];
  document.getElementById('g-cur').textContent   = currentIdx + 1;
  document.getElementById('g-tot').textContent   = gamePhotos.length;
  document.getElementById('g-photo').src         = p.url;
  document.getElementById('g-season').textContent = p.date;

  const dirEl = document.getElementById('g-direction');
  dirEl.textContent = p.direction;
  dirEl.className   = 'hint-chip ' + (p.direction === 'SoBo' ? 'hint-sobo' : 'hint-nobo');

  const input = document.getElementById('mile-input');
  input.value = '';
  document.getElementById('trail-slider').value = 0;
  updateThumbColors(0);
  if (window.resetPhotoZoom) window.resetPhotoZoom();
  showScreen('screen-guess');
  setTimeout(() => input.focus(), 80);
  startTimer();
}}

function submitGuess() {{
  const raw = document.getElementById('mile-input').value.trim();
  if (!raw) return;
  stopTimer();
  processGuess(parseFloat(raw), false);
}}

function processGuess(guess, timedOut) {{
  stopTimer();
  const p = gamePhotos[currentIdx];
  const trueMile = parseFloat(p.mile);
  const score = timedOut ? Math.round(NO_ANSWER_PENALTY) : calcScore(guess, trueMile);
  scores.push(score);
  guesses.push(timedOut ? null : guess);
  showResultScreen(p, guess, timedOut, score);
}}

function showResultScreen(p, guess, timedOut, score) {{
  if (window.resetResultZoom) window.resetResultZoom();
  const trueMile = parseFloat(p.mile);
  const runTotal = scores.reduce((a, b) => a + b, 0);

  // Photo
  document.getElementById('r-photo').src = p.url;

  // Metadata chips
  document.getElementById('r-mile').textContent    = `Mile ${{p.mile}}`;
  document.getElementById('r-section').textContent = p.section;
  document.getElementById('r-date').textContent    = p.date;
  document.getElementById('r-dir').textContent     = p.direction;

  // True mile / guess comparison
  document.getElementById('r-true-mile').textContent  = fmt(trueMile);
  document.getElementById('r-your-guess').textContent = timedOut ? '—' : fmt(guess);

  // Verdict
  const stVerdict = document.getElementById('st-verdict');
  if (timedOut) {{
    stVerdict.textContent = 'Timed out';
    stVerdict.className   = 'rsc-verdict timeout';
  }} else {{
    const v = getVerdictInfo(guess, trueMile);
    stVerdict.textContent = v.text;
    stVerdict.className   = 'rsc-verdict ' + v.cls;
  }}

  // Round score
  const stRound = document.getElementById('st-round');
  if (score === 0) {{
    stRound.textContent = '0  🎯';
    stRound.className   = 'rsc-score-val perfect';
  }} else {{
    stRound.textContent = `${{fmt(score)}} mi`;
    stRound.className   = 'rsc-score-val';
  }}

  // Running total
  document.getElementById('st-total').textContent = `${{fmt(runTotal)}} mi`;
  document.getElementById('st-total').className   = 'rsc-score-val';

  const isLast = currentIdx === gamePhotos.length - 1;
  document.getElementById('btn-next').textContent = isLast ? 'See Final Results →' : 'Next Photo →';

  showScreen('screen-result');
}}

function nextPhoto() {{
  currentIdx++;
  currentIdx >= gamePhotos.length ? showEndScreen() : showGuessScreen();
}}

function showEndScreen() {{
  const total = scores.reduce((a, b) => a + b, 0);
  document.getElementById('final-score').textContent = fmt(total);
  const avg = Math.round(total / gamePhotos.length);
  document.getElementById('final-avg').textContent = `On average, you were ${{fmt(avg)}} miles off.`;

  const tbody = document.getElementById('end-tbody');
  tbody.innerHTML = '';
  gamePhotos.forEach((p, i) => {{
    const guess     = guesses[i];
    const score     = scores[i];
    const trueMile  = parseFloat(p.mile);

    const tr = document.createElement('tr');

    // Thumbnail cell (clickable → lightbox)
    const tdThumb = document.createElement('td');
    tdThumb.className = 'td-thumb';
    tdThumb.innerHTML = `<img class="et-thumb" src="${{p.url}}" alt=""
      onclick="openLightbox('${{p.url}}', 'Mile ${{p.mile}} · ${{p.section}} · ${{p.direction}}')">`;

    // Your guess
    const tdGuess = document.createElement('td');
    if (guess === null) {{
      tdGuess.className   = 'td-guess no-answer';
      tdGuess.textContent = 'timed out';
    }} else {{
      tdGuess.className   = 'td-guess';
      tdGuess.textContent = fmt(guess);
    }}

    // True mile
    const tdMile = document.createElement('td');
    tdMile.className   = 'td-mile';
    tdMile.textContent = fmt(trueMile);

    // Score
    const tdScore = document.createElement('td');
    tdScore.className   = 'td-score ' + (score === 0 ? 'perfect' : 'off');
    tdScore.textContent = score === 0 ? '✓ 0' : fmt(score);

    tr.append(tdThumb, tdMile, tdGuess, tdScore);
    tbody.appendChild(tr);
  }});

  showScreen('screen-end');
  // Pre-select + preload next game's photos while user reads the end screen
  prepareNextGame();
}}

// ── Lightbox ──────────────────────────────────────────────
function openLightbox(url, caption) {{
  document.getElementById('lb-img').src          = url;
  document.getElementById('lb-caption').textContent = caption;
  document.getElementById('lightbox').classList.add('open');
}}

function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('open');
  document.getElementById('lb-img').src = '';
}}

// Close lightbox on backdrop click
document.getElementById('lightbox').addEventListener('click', e => {{
  if (e.target === document.getElementById('lightbox')) closeLightbox();
}});

// Enter to submit guess
document.getElementById('mile-input').addEventListener('keydown', e => {{
  if (e.key === 'Enter') submitGuess();
}});

// Trail slider ↔ mile input: bidirectional sync + thumb colour update
const trailSlider = document.getElementById('trail-slider');
trailSlider.addEventListener('input', () => {{
  const v = parseFloat(trailSlider.value);
  document.getElementById('mile-input').value = v;
  updateThumbColors(v);
}});
document.getElementById('mile-input').addEventListener('input', () => {{
  const v = parseFloat(document.getElementById('mile-input').value);
  if (!isNaN(v) && v >= 0 && v <= 2655) {{
    trailSlider.value = Math.round(v);
    updateThumbColors(v);
  }}
}});

// ── Pinch-to-zoom + pan (shared factory) ─────────────────
// Used by both the guess screen and the result screen.
// Zoom anchors to the midpoint of the two fingers (focal point), so the
// spot you pinch stays under your fingers rather than the image jumping.
//
// Formula: when scale changes by ratio r around focal point (fX, fY):
//   newPanX = fX + (panX - fX) * r
//   newPanY = fY + (panY - fY) * r
// fX/fY are relative to the frame centre (matching transform-origin:centre).
function makePinchZoom(frameEl, photoEl, resetName) {{
  let scale = 1, panX = 0, panY = 0;
  let startDist = 0, startScale = 1, startRect = null;
  let lastX = 0, lastY = 0;

  function clamp(v, lo, hi) {{ return v < lo ? lo : v > hi ? hi : v; }}

  function applyTransform() {{
    const maxPanX = clamp((scale - 1) * frameEl.clientWidth  / 2, 0, Infinity);
    const maxPanY = clamp((scale - 1) * frameEl.clientHeight / 2, 0, Infinity);
    panX = clamp(panX, -maxPanX, maxPanX);
    panY = clamp(panY, -maxPanY, maxPanY);
    photoEl.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{scale}})`;
  }}

  function touchDist(t) {{
    return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY);
  }}

  window[resetName] = function() {{
    scale = 1; panX = 0; panY = 0;
    photoEl.style.transform = '';
  }};

  frameEl.addEventListener('touchstart', e => {{
    if (e.touches.length === 2) {{
      startDist  = touchDist(e.touches);
      startScale = scale;
      startRect  = frameEl.getBoundingClientRect(); // cache for focal-point calc
      e.preventDefault();
    }} else if (e.touches.length === 1 && scale > 1) {{
      lastX = e.touches[0].clientX;
      lastY = e.touches[0].clientY;
    }}
  }}, {{ passive: false }});

  frameEl.addEventListener('touchmove', e => {{
    if (e.touches.length === 2) {{
      const newScale = clamp(startScale * touchDist(e.touches) / startDist, 1, 6);
      // Focal point = finger midpoint, relative to frame centre
      const focalX = (e.touches[0].clientX + e.touches[1].clientX) / 2
                   - (startRect.left + startRect.width  / 2);
      const focalY = (e.touches[0].clientY + e.touches[1].clientY) / 2
                   - (startRect.top  + startRect.height / 2);
      // Shift pan so the focal point stays fixed as scale changes
      const ratio = newScale / scale;
      panX   = focalX + (panX - focalX) * ratio;
      panY   = focalY + (panY - focalY) * ratio;
      scale  = newScale;
      applyTransform();
      e.preventDefault();
    }} else if (e.touches.length === 1 && scale > 1) {{
      panX += e.touches[0].clientX - lastX;
      panY += e.touches[0].clientY - lastY;
      lastX  = e.touches[0].clientX;
      lastY  = e.touches[0].clientY;
      applyTransform();
      e.preventDefault();
    }}
  }}, {{ passive: false }});

  frameEl.addEventListener('touchend', e => {{
    if (e.touches.length === 0 && scale <= 1.05) window[resetName]();
  }});
}}

// Guess screen
makePinchZoom(
  document.querySelector('#screen-guess .photo-frame'),
  document.getElementById('g-photo'),
  'resetPhotoZoom'
);

// Result screen
makePinchZoom(
  document.querySelector('#screen-result .result-photo-wrap'),
  document.getElementById('r-photo'),
  'resetResultZoom'
);

// Block iOS from zooming the whole page on two-finger gestures outside photo areas
document.addEventListener('touchmove', e => {{
  if (e.touches.length > 1) {{
    const guessFrame  = document.querySelector('#screen-guess .photo-frame');
    const resultFrame = document.querySelector('#screen-result .result-photo-wrap');
    if (!guessFrame.contains(e.target) && !resultFrame.contains(e.target)) {{
      e.preventDefault();
    }}
  }}
}}, {{ passive: false }});

// ── Kick everything off ───────────────────────────────────
// Pre-select photos then immediately start — no separate start screen.
prepareNextGame();
startGame();
</script>
</body>
</html>
"""

with open(OUT_PATH, "w") as f:
    f.write(html)

print(f"Built {OUT_PATH}")
print(f"  {len(v1_photos)} v1-demo photos available")
