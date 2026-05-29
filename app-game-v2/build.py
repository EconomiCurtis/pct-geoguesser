# ──────────────────────────────────────────────────────────────────────────────
# build.py  —  PCT GeoGuesser  (game v2 — scored / authenticated)
#
# Reads misc/photos.csv (v2-scored pool) and generates a self-contained
# index.html with Google OAuth (via Supabase), a hiker profile signup,
# scored gameplay, and a post-game rank display.
#
# Prerequisites:
#   • misc/supabase_config.py — SUPABASE_URL and SUPABASE_ANON_KEY
#   • In Supabase dashboard → Authentication → URL Configuration:
#       Site URL:     https://pct-geoguesser.pages.dev
#       Redirect URL: https://pct-geoguesser.pages.dev/game/
#
# To rebuild after editing:
#   python3 app-game-v2/build.py
#
# To deploy:
#   cp app-landing/index.html          deploy/index.html
#   cp app-game-v1-testing/index.html  deploy/practice/index.html
#   cp app-game-v2/index.html          deploy/game/index.html
#   npx wrangler pages deploy deploy/ --project-name=pct-geoguesser
# ──────────────────────────────────────────────────────────────────────────────

import csv
import json
import os
import sys

HERE     = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "misc"))
from supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY

CSV_PATH      = os.path.join(HERE, "..", "misc", "photos.csv")
OUT_PATH      = os.path.join(HERE, "index.html")
MISC_BASE_URL = "https://pct-geoguesser.pages.dev/misc"

with open(CSV_PATH) as f:
    rows = list(csv.DictReader(f))

v2_photos = [r for r in rows if r.get("version") == "v2-scored"]

game_data = json.dumps(
    [
        {
            "id":        r["id"],
            "mile":      r["mile"],
            "direction": r["direction"],
            "section":   r["section"],
            "date":      r["date"],
            "url":       r["url"],
        }
        for r in v2_photos
    ]
)

# ── Trail slider: section colours + generated HTML ────────────
_TRAIL_MAX = 2655.5
_SECTIONS = [
    {"abbr": "S. California", "start":    0.0, "end":  702.1, "color": "#c8a96e", "tcol": "#d4b07a", "bg": "rgba(200,169,110,.2)"},
    {"abbr": "Sierra",        "start":  702.1, "end": 1092.3, "color": "#d8d8d8", "tcol": "#e8e8e8", "bg": "rgba(240,246,252,.12)"},
    {"abbr": "N. California", "start": 1092.3, "end": 1692.0, "color": "#2ab062", "tcol": "#4fca84", "bg": "rgba(42,176,98,.2)"},
    {"abbr": "Oregon",        "start": 1692.0, "end": 2147.0, "color": "#008080", "tcol": "#5fd4d4", "bg": "rgba(0,128,128,.2)"},
    {"abbr": "Washington",    "start": 2147.0, "end": 2655.5, "color": "#1D502E", "tcol": "#7ecb96", "bg": "rgba(29,80,46,.3)"},
]

def _mpct(m):
    return f"{m / _TRAIL_MAX * 100:.2f}%"

_grad = ", ".join(
    f"{s['color']} {_mpct(s['start'])} {_mpct(s['end'])}" for s in _SECTIONS
)
slider_gradient = f"linear-gradient(to right, {_grad})"

_bounds = [s["start"] for s in _SECTIONS] + [_TRAIL_MAX]
_marks  = []
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

_sec_bars = []
for _s in _SECTIONS:
    _miles = _s["end"] - _s["start"]
    _sec_bars.append(
        f'<div class="ts-sec" style="flex:{_miles:.1f};'
        f'background:{_s["bg"]};color:{_s["tcol"]}">{_s["abbr"]}</div>'
    )
slider_sections = "\n      ".join(_sec_bars)

# ─────────────────────────────────────────────────────────────────────────────

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>PCT GeoGuesser — Scored</title>
<!-- Open Graph / social preview -->
<meta property="og:type"        content="website">
<meta property="og:url"         content="https://pct-geoguesser.pages.dev/game/">
<meta property="og:title"       content="PCT GeoGuesser — Scored">
<meta property="og:description" content="Compete on the global PCT leaderboard.">
<meta property="og:image"       content="{MISC_BASE_URL}/preview.png">
<meta name="twitter:card"        content="summary_large_image">
<meta name="twitter:title"       content="PCT GeoGuesser — Scored">
<meta name="twitter:description" content="Compete on the global PCT leaderboard.">
<meta name="twitter:image"       content="{MISC_BASE_URL}/preview.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="icon" type="image/png" href="{MISC_BASE_URL}/pct-geoguesser-favicon.png">
<link rel="apple-touch-icon" href="{MISC_BASE_URL}/pct-geoguesser-favicon.png">
<meta name="theme-color" content="#0d1117">
<meta name="description" content="Compete on the global PCT GeoGuesser leaderboard. Sign in with Google.">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg:        #0d1117;
  --surface:   #161b22;
  --surface2:  #21262d;
  --border:    #30363d;
  --text:      #f0f6fc;
  --muted:     #8b949e;
  --pct-green: #1D502E;
  --pct-teal:  #008080;
  --pct-blue:  #1C2D50;
  --pct-white: #FFFFFF;
  --timer-red: #dc2626;
  --perfect:   #008080;
  --nobo-col:  #2ab062;
  --sobo-col:  #c8a96e;
  --north-col: #6fd4a0;
  --south-col: #c8a96e;
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

/* ── Loading / spinner ───────────────────────────────────── */
#screen-loading {{
  align-items: center; justify-content: center; gap: 14px;
}}
.loading-spinner {{
  width: 36px; height: 36px;
  border: 3px solid var(--border); border-top-color: var(--pct-teal);
  border-radius: 50%; animation: spin .8s linear infinite;
}}
.loading-spinner-sm {{
  width: 14px; height: 14px; flex-shrink: 0;
  border: 2px solid var(--border); border-top-color: var(--pct-teal);
  border-radius: 50%; animation: spin .8s linear infinite;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
.loading-text {{ color: var(--muted); font-size: 14px; }}

/* ── Shared centred-page layout (auth / signup / start) ─── */
.page-center {{
  align-items: center; justify-content: center; overflow-y: auto;
  padding: 24px 20px; gap: 18px; text-align: center;
}}

/* ── Logo ─────────────────────────────────────────────────── */
.logo-pair {{
  display: flex; align-items: center; justify-content: center;
}}
.logo-box {{
  background: #fff; border-radius: 10px;
  border: 3px solid #000; box-shadow: 0 0 0 3px #fff;
  padding: 12px; display: inline-flex; align-items: center;
  justify-content: center; gap: 16px;
}}
.logo-pair img {{ object-fit: contain; }}
.logo-old {{ height: 94px;  width: auto; }}
.logo-new {{ height: 84px;  width: auto; }}

/* ── Heading ─────────────────────────────────────────────── */
h1 {{
  font-size: clamp(26px, 6vw, 46px); font-weight: 800; line-height: 1.1;
  color: var(--pct-white); text-shadow: 0 0 30px rgba(0,128,128,.4);
}}
h1 span {{ color: var(--pct-teal); }}

.start-sub {{
  color: var(--muted); font-size: 14px; max-width: 360px; line-height: 1.5;
}}

/* ── Buttons ─────────────────────────────────────────────── */
.btn-green {{
  background: var(--pct-green); color: var(--pct-white);
  border: none; border-radius: 10px;
  padding: 13px 36px; font-size: 16px; font-weight: 700;
  cursor: pointer; transition: filter .15s, transform .1s;
  letter-spacing: .01em; white-space: nowrap;
}}
.btn-green:hover {{ filter: brightness(1.25); transform: translateY(-1px); }}
.btn-green:active {{ transform: translateY(0); }}
.btn-green:disabled {{ opacity: .6; cursor: default; transform: none; }}

.btn-outline {{
  background: transparent; color: var(--text);
  border: 1px solid var(--border); border-radius: 10px;
  padding: 13px; font-size: 15px; font-weight: 600;
  cursor: pointer; width: 100%; transition: background .15s, border-color .15s;
  text-decoration: none; display: block; text-align: center;
}}
.btn-outline:hover {{ background: var(--surface2); border-color: var(--muted); }}

/* ── Google sign-in button ───────────────────────────────── */
.btn-google {{
  display: flex; align-items: center; justify-content: center; gap: 12px;
  background: #fff; color: #3c4043;
  border: 1px solid #dadce0; border-radius: 10px;
  padding: 13px 24px; font-size: 16px; font-weight: 600;
  cursor: pointer; transition: box-shadow .15s;
  font-family: 'Open Sans', Arial, sans-serif;
}}
.btn-google:hover {{ box-shadow: 0 2px 10px rgba(0,0,0,.35); }}
.btn-google:disabled {{ opacity: .6; cursor: default; box-shadow: none; }}

/* ── Rules card ──────────────────────────────────────────── */
.rules-card {{
  background: var(--surface); border: 1px solid var(--pct-green);
  border-radius: 12px; padding: 16px 18px;
  max-width: 400px; width: 100%; text-align: left;
}}
.rules-card h3 {{
  font-size: 10px; text-transform: uppercase;
  letter-spacing: .12em; color: var(--pct-teal); margin-bottom: 10px;
}}
.rules-card ul + h3 {{ margin-top: 14px; }}
.rules-card ul {{ list-style: none; display: flex; flex-direction: column; gap: 8px; }}
.rules-card li {{
  display: flex; align-items: baseline; gap: 9px;
  font-size: 13px; line-height: 1.45; color: var(--text);
}}
.rules-card li::before {{ content: '▸'; color: var(--pct-green); flex-shrink: 0; }}
.rules-card a {{ color: var(--pct-teal); text-decoration: underline; }}
.rules-card a:hover {{ color: #5fd4d4; }}

.about-link {{ font-size: 12px; color: var(--muted); text-align: center; }}

/* ══════════════════════════════════════════════════════════
   AUTH SCREEN
══════════════════════════════════════════════════════════ */
.auth-sub {{
  color: var(--muted); font-size: 14px; max-width: 320px; line-height: 1.5;
}}
.auth-practice {{
  font-size: 13px; color: var(--muted);
}}
.auth-practice a {{ color: var(--pct-teal); text-decoration: underline; }}
.auth-practice a:hover {{ color: #5fd4d4; }}

/* ══════════════════════════════════════════════════════════
   SIGNUP SCREEN
══════════════════════════════════════════════════════════ */
.signup-card {{
  background: var(--surface); border: 1px solid var(--pct-green);
  border-radius: 12px; padding: 20px 22px;
  max-width: 400px; width: 100%; text-align: left;
  display: flex; flex-direction: column; gap: 16px;
}}
.signup-card h3 {{
  font-size: 10px; text-transform: uppercase;
  letter-spacing: .12em; color: var(--pct-teal);
}}
.form-field {{ display: flex; flex-direction: column; gap: 6px; }}
.form-label {{
  font-size: 11px; text-transform: uppercase;
  letter-spacing: .09em; color: var(--muted);
}}
.form-input {{
  background: var(--surface2); color: var(--text);
  border: 2px solid var(--border); border-radius: 8px;
  padding: 10px 12px; font-size: 16px; outline: none;
  font-family: inherit;
}}
.form-input:focus {{ border-color: var(--pct-teal); }}
.form-hint {{ font-size: 11px; color: var(--muted); }}
.form-error {{ font-size: 12px; color: #dc2626; min-height: 16px; }}
textarea.form-input {{ resize: vertical; min-height: 80px; font-size: 14px; line-height: 1.5; }}
.char-count {{ font-size: 11px; color: var(--muted); font-weight: 400; }}
.signup-cancel {{ font-size: 13px; color: var(--muted); text-decoration: none; text-align: center; }}
.signup-cancel:hover {{ color: var(--text); }}

/* ══════════════════════════════════════════════════════════
   START SCREEN (authenticated)
══════════════════════════════════════════════════════════ */
.greeting {{
  font-size: 17px; font-weight: 600; color: var(--muted);
}}
.greeting-link {{
  color: var(--text); text-decoration: none; transition: color .15s;
}}
.greeting-link:hover {{ color: var(--pct-teal); text-decoration: underline; }}

.start-links {{
  display: flex; gap: 18px; align-items: center; font-size: 13px;
}}
.start-links a {{
  color: var(--muted); text-decoration: none; transition: color .15s;
}}
.start-links a:hover {{ color: var(--text); }}
.start-links .dot {{ color: var(--border); }}

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
.timer-bar-track {{ width: 100%; height: 7px; background: var(--surface2); flex-shrink: 0; }}
.timer-bar-fill {{ height: 100%; background: var(--timer-red); transition: width .95s linear; }}
.timer-num {{
  font-size: 20px; font-weight: 800; color: var(--timer-red);
  font-variant-numeric: tabular-nums; min-width: 32px; text-align: right;
}}
.photo-frame {{
  flex: 1; min-height: 0; position: relative;
  display: flex; align-items: center; justify-content: center;
  background: #000; overflow: hidden;
  touch-action: none;
}}
.photo-frame img {{
  max-width: 100%; max-height: 100%; object-fit: contain; display: block;
  transform-origin: center center; will-change: transform;
}}
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
.hint-season  {{ background: rgba(29,80,46,.25);   color: #7ecb96;          border-color: var(--pct-green); }}
.hint-nobo    {{ background: rgba(42,176,98,.18);   color: #6fd4a0;          border-color: var(--nobo-col);  }}
.hint-sobo    {{ background: rgba(200,169,110,.18); color: var(--sobo-col);  border-color: var(--sobo-col);  }}
.input-section {{
  flex-shrink: 0; background: var(--surface); padding: 12px 14px;
  display: flex; flex-direction: column; gap: 8px;
}}
.input-label {{ font-size: 11px; color: var(--muted); text-align: center; text-transform: uppercase; letter-spacing: .09em; }}
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
.trail-slider-wrap {{ display: flex; flex-direction: column; gap: 4px; padding-top: 2px; }}
#trail-slider {{
  -webkit-appearance: none; appearance: none;
  width: 100%; height: 6px; border-radius: 3px;
  background: {slider_gradient};
  outline: none; cursor: pointer;
  --thumb-left:   #d4b07a;
  --thumb-center: #c8a96e;
  --thumb-right:  #c8a96e;
  --thumb-glow:   rgba(200,169,110,.35);
}}
#trail-slider::-webkit-slider-thumb {{
  -webkit-appearance: none; width: 22px; height: 22px;
  background: linear-gradient(90deg, var(--thumb-left) 0%, var(--thumb-center) 50%, var(--thumb-right) 100%);
  border-radius: 50%; border: 2px solid rgba(255,255,255,.2);
  cursor: grab; box-shadow: 0 2px 6px rgba(0,0,0,.7), 0 0 0 3px var(--thumb-glow);
}}
#trail-slider::-moz-range-thumb {{
  width: 22px; height: 22px;
  background: linear-gradient(90deg, var(--thumb-left) 0%, var(--thumb-center) 50%, var(--thumb-right) 100%);
  border-radius: 50%; border: 2px solid rgba(255,255,255,.2);
  cursor: grab; box-shadow: 0 2px 6px rgba(0,0,0,.7);
}}
.trail-marks {{ position: relative; height: 14px; }}
.trail-marks span {{
  position: absolute; font-size: 9px; color: var(--muted);
  font-variant-numeric: tabular-nums; line-height: 1; white-space: nowrap;
}}
.trail-sections {{ display: flex; width: 100%; gap: 1px; border-radius: 3px; overflow: hidden; }}
.ts-sec {{
  text-align: center; font-size: 9px; font-weight: 600;
  padding: 2px 1px; overflow: hidden; white-space: nowrap; letter-spacing: .02em;
}}
@media (pointer: coarse) {{
  #trail-slider {{ height: 8px; }}
  #trail-slider::-webkit-slider-thumb {{ width: 32px; height: 32px; }}
  #trail-slider::-moz-range-thumb    {{ width: 32px; height: 32px; }}
}}

/* ══════════════════════════════════════════════════════════
   RESULT SCREEN
══════════════════════════════════════════════════════════ */
#screen-result {{ overflow-y: auto; }}
.result-score-wrap {{ flex-shrink: 0; display: flex; justify-content: center; padding: 12px 16px 0; }}
.result-score-card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px 20px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  width: 100%; max-width: 420px;
}}
.rsc-cols {{ display: flex; align-items: flex-start; justify-content: center; width: 100%; }}
.rsc-col  {{ flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; }}
.rsc-divider {{ width: 1px; background: var(--border); align-self: stretch; margin: 0 16px; }}
.rsc-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: .09em; color: var(--muted); }}
.rsc-num   {{ font-size: 26px; font-weight: 800; font-variant-numeric: tabular-nums; color: var(--text); }}
.rsc-num.true-mile {{ color: var(--pct-teal); }}
.rsc-guess-was {{ font-size: 9px; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: -4px; }}
.rsc-verdict {{ font-size: 22px; font-weight: 800; text-align: center; line-height: 1.2; }}
.rsc-verdict.spoton  {{ color: var(--perfect); }}
.rsc-verdict.north   {{ color: var(--north-col); }}
.rsc-verdict.south   {{ color: var(--south-col); }}
.rsc-verdict.timeout {{ color: var(--muted); font-size: 16px; font-weight: 600; }}
.rsc-scores {{ width: 100%; display: flex; flex-direction: column; gap: 4px; border-top: 1px solid var(--border); padding-top: 8px; }}
.rsc-score-row   {{ display: flex; justify-content: space-between; align-items: baseline; }}
.rsc-score-label {{ font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }}
.rsc-score-val   {{ font-size: 15px; font-weight: 700; font-variant-numeric: tabular-nums; }}
.rsc-score-val.perfect {{ color: var(--perfect); }}
.result-photo-wrap {{
  flex: 1; min-height: 180px; max-height: 50vh; position: relative;
  display: flex; align-items: center; justify-content: center;
  background: #000; overflow: hidden; margin-top: 10px;
  touch-action: none;
}}
.result-photo-wrap img {{
  width: 100%; height: 100%; object-fit: contain; display: block;
  transform-origin: center center; will-change: transform;
}}
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
.a-chip.mile {{ color: var(--pct-teal); border-color: var(--pct-teal); background: rgba(0,128,128,.12); font-size: 13px; font-weight: 700; }}
.result-actions {{ flex-shrink: 0; padding: 12px 14px; background: var(--surface); border-top: 1px solid var(--border); }}

/* ══════════════════════════════════════════════════════════
   END SCREEN
══════════════════════════════════════════════════════════ */
#screen-end {{ overflow-y: auto; padding: 20px 14px 32px; align-items: center; gap: 18px; }}
.end-title {{ font-size: clamp(22px, 5vw, 34px); font-weight: 800; text-align: center; }}
.final-box {{
  background: var(--surface); border: 1px solid var(--pct-teal);
  border-radius: 14px; padding: 18px 28px; text-align: center;
  width: 100%; max-width: 300px;
}}
.final-box .fb-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: .12em; color: var(--muted); margin-bottom: 5px; }}
.final-box .fb-score {{ font-size: 52px; font-weight: 800; line-height: 1; color: var(--pct-teal); font-variant-numeric: tabular-nums; }}
.final-box .fb-unit  {{ font-size: 12px; color: var(--muted); margin-top: 3px; }}
.final-avg {{ font-size: 16px; font-weight: 600; color: var(--muted); text-align: center; margin-top: -8px; }}

/* Submit / rank card */
.submit-card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px 20px;
  width: 100%; max-width: 400px; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}}
.submit-loading {{
  display: flex; align-items: center; gap: 10px;
  color: var(--muted); font-size: 14px;
}}
.submit-success {{ display: none; flex-direction: column; align-items: center; gap: 8px; }}
.rank-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); }}
.rank-num   {{ font-size: 48px; font-weight: 800; line-height: 1; color: var(--pct-teal); font-variant-numeric: tabular-nums; }}
.rank-sub   {{ font-size: 12px; color: var(--muted); }}
.rank-lb-link {{ font-size: 13px; color: var(--pct-teal); text-decoration: underline; }}
.rank-lb-link:hover {{ color: #5fd4d4; }}
.submit-error {{ display: none; font-size: 13px; color: #dc2626; }}

.end-table-wrap {{ width: 100%; max-width: 580px; overflow-x: auto; }}
.end-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.end-table th {{ padding: 6px 10px; font-size: 10px; text-transform: uppercase; letter-spacing: .09em; border-bottom: 1px solid var(--border); white-space: nowrap; font-weight: 700; }}
.end-table th.th-photo {{ text-align: left; color: var(--muted); }}
.end-table th.th-guess {{ text-align: right; color: var(--sobo-col); }}
.end-table th.th-mile  {{ text-align: right; color: var(--pct-teal); }}
.end-table th.th-score {{ text-align: right; color: #7ecb96; }}
.end-table td {{ padding: 6px 10px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
.end-table tr:last-child td {{ border-bottom: none; }}
.end-table .td-thumb {{ width: 52px; padding: 4px 10px 4px 0; }}
.et-thumb {{ width: 52px; height: 38px; object-fit: cover; border-radius: 4px; cursor: pointer; display: block; transition: opacity .15s; border: 1px solid var(--border); }}
.et-thumb:hover {{ opacity: .8; border-color: var(--pct-teal); }}
.end-table .td-guess {{ text-align: right; font-weight: 700; color: var(--sobo-col); font-variant-numeric: tabular-nums; }}
.end-table .td-guess.no-answer {{ color: var(--muted); font-weight: 400; font-size: 11px; }}
.end-table .td-mile  {{ text-align: right; font-weight: 700; color: var(--pct-teal); font-variant-numeric: tabular-nums; }}
.end-table .td-score {{ text-align: right; font-weight: 700; font-variant-numeric: tabular-nums; }}
.end-table .td-score.perfect {{ color: var(--pct-teal); }}
.end-table .td-score.off     {{ color: var(--muted); }}

.end-actions {{ display: flex; gap: 10px; width: 100%; max-width: 300px; }}
.end-actions .btn-green  {{ flex: 1; padding: 13px; }}
.end-actions .btn-outline {{ flex: 1; }}

/* ── Lightbox ─────────────────────────────────────────── */
#lightbox {{ display: none; position: fixed; inset: 0; z-index: 100; background: rgba(0,0,0,.92); align-items: center; justify-content: center; flex-direction: column; gap: 12px; padding: 16px; }}
#lightbox.open {{ display: flex; }}
#lightbox img {{ max-width: 100%; max-height: 80vh; object-fit: contain; border-radius: 6px; }}
.lightbox-caption {{ font-size: 13px; color: var(--muted); text-align: center; }}
.lightbox-close {{ position: absolute; top: 14px; right: 14px; background: var(--surface2); color: var(--text); border: 1px solid var(--border); border-radius: 50%; width: 36px; height: 36px; font-size: 18px; line-height: 36px; text-align: center; cursor: pointer; transition: background .15s; }}
.lightbox-close:hover {{ background: var(--border); }}

/* ── Mobile logo scale-up ─────────────────────────────── */
@media (max-width: 640px) {{
  .logo-box {{ padding: 18px; gap: 24px; }}
  .logo-old {{ height: 140px; }}
  .logo-new {{ height: 126px; }}
}}

/* ── Desktop scale-up ─────────────────────────────────── */
@media (min-width: 900px) {{
  .page-center {{ gap: 26px; }}
  .logo-old {{ height: 117px; }}
  .logo-new {{ height: 106px; }}
  h1 {{ font-size: clamp(52px, 5.5vw, 88px); }}
  .start-sub {{ font-size: 18px; max-width: 520px; }}
  .rules-card {{ max-width: 580px; padding: 22px 26px; }}
  .rules-card h3 {{ font-size: 12px; margin-bottom: 14px; }}
  .rules-card li {{ font-size: 16px; }}
  .btn-green {{ font-size: 18px; padding: 15px 44px; }}
  .signup-card {{ max-width: 480px; }}
}}
</style>
</head>
<body>

<!-- Supabase JS — must load before our script -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>

<!-- ════════════════ LOADING ════════════════ -->
<div id="screen-loading" class="screen active">
  <div class="loading-spinner"></div>
  <p class="loading-text">Loading…</p>
</div>

<!-- ════════════════ AUTH ════════════════ -->
<div id="screen-auth" class="screen page-center">
  <div class="logo-pair">
    <div class="logo-box">
      <img src="{MISC_BASE_URL}/pct-orig-logo.webp" class="logo-old" alt="PCT original logo">
      <img src="{MISC_BASE_URL}/pct-new-logo.webp"  class="logo-new" alt="PCT shield logo">
    </div>
  </div>
  <h1>PCT <span>GeoGuesser</span></h1>
  <p class="auth-sub">Sign in to compete on the global leaderboard. Your scores are tracked and ranked against other PCT hikers.</p>
  <button class="btn-google" id="btn-google" onclick="signInWithGoogle()">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="20" height="20">
      <path fill="#FFC107" d="M43.6 20H24v8h11.3c-1.1 5.4-5.8 8-11.3 8-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l5.7-5.7C34.1 4.1 29.3 2 24 2 12.9 2 4 10.9 4 22s8.9 20 20 20 20-8.9 20-20c0-1.4-.1-2.7-.4-4z"/>
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.1 8 2.9l5.7-5.7C34.1 4.1 29.3 2 24 2c-7.7 0-14.4 4.3-17.7 10.7z"/>
      <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2A11.9 11.9 0 0 1 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"/>
      <path fill="#1976D2" d="M43.6 20H42V20H24v8h11.3a12 12 0 0 1-4.1 5.6l6.2 5.2C36.9 39.2 44 34 44 24c0-1.4-.1-2.7-.4-4z"/>
    </svg>
    Sign in with Google
  </button>
  <p class="auth-practice">No account? <a href="/practice/">Try Practice Mode</a> — no login required.</p>
</div>

<!-- ════════════════ SIGNUP ════════════════ -->
<div id="screen-signup" class="screen page-center">
  <div class="logo-pair">
    <div class="logo-box">
      <img src="{MISC_BASE_URL}/pct-orig-logo.webp" class="logo-old" alt="PCT original logo">
      <img src="{MISC_BASE_URL}/pct-new-logo.webp"  class="logo-new" alt="PCT shield logo">
    </div>
  </div>
  <h1>PCT <span>GeoGuesser</span></h1>
  <p class="start-sub" id="signup-subtitle">One-time setup — your name and year appear on the leaderboard.</p>
  <div class="signup-card">
    <h3>Your Hiker Profile</h3>
    <div class="form-field">
      <label class="form-label" for="trail-name-input">Trail Name</label>
      <input type="text" id="trail-name-input" class="form-input"
             placeholder="e.g. Whiskey Jack" maxlength="60" autocomplete="off">
      <p class="form-hint">Shown on the leaderboard next to your scores.</p>
    </div>
    <div class="form-field">
      <label class="form-label" for="pct-year-input">PCT Year</label>
      <input type="text" id="pct-year-input" class="form-input"
             placeholder="e.g. 2025, 2024 / 2026, planning 2027" maxlength="40" autocomplete="off">
      <p class="form-hint">When did / will you hike? Shown below your trail name.</p>
    </div>
    <div class="form-field">
      <label class="form-label" for="about-input">About <span class="char-count" id="about-char-count">(0/500)</span></label>
      <textarea id="about-input" class="form-input" rows="3"
                placeholder="Optional: tell other hikers a bit about yourself…"
                maxlength="500" autocomplete="off"
                oninput="updateAboutCount()"></textarea>
      <p class="form-hint">Shown on your hiker profile page. Optional.</p>
    </div>
    <p class="form-error" id="signup-error"></p>
    <button class="btn-green" id="btn-save-profile" onclick="saveProfile()">Save and Play →</button>
    <p id="save-slow-hint" class="form-hint" style="display:none;text-align:center">Taking a moment — first saves can be slow ☁️</p>
    <a href="#" id="signup-cancel" class="signup-cancel" style="display:none" onclick="cancelEditProfile(); return false;">← Cancel</a>
  </div>
</div>

<!-- ════════════════ START (authenticated) ════════════════ -->
<div id="screen-start" class="screen page-center">
  <div class="logo-pair">
    <div class="logo-box">
      <img src="{MISC_BASE_URL}/pct-orig-logo.webp" class="logo-old" alt="PCT original logo">
      <img src="{MISC_BASE_URL}/pct-new-logo.webp"  class="logo-new" alt="PCT shield logo">
    </div>
  </div>
  <h1>PCT <span>GeoGuesser</span></h1>
  <p class="greeting">Hey, <a id="greeting-name" class="greeting-link" href="#">…</a>! 👋</p>
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
  <button class="btn-green" onclick="startGame()">Start Scored Game →</button>
  <div class="start-links">
    <a href="/leaderboard/">Leaderboard</a>
    <span class="dot">·</span>
    <a href="#" onclick="showEditProfile(); return false;">Edit Profile</a>
    <span class="dot">·</span>
    <a href="#" onclick="signOut(); return false;">Sign out</a>
  </div>
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
  <div class="result-score-wrap">
    <div class="result-score-card">
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
      <div class="rsc-guess-was">Your Guess Was</div>
      <div class="rsc-verdict" id="st-verdict"></div>
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
  <div class="result-photo-wrap">
    <img id="r-photo" src="" alt="">
  </div>
  <div class="answer-meta-bar">
    <span class="a-chip mile" id="r-mile"></span>
    <span class="a-chip" id="r-section"></span>
    <span class="a-chip" id="r-date"></span>
    <span class="a-chip" id="r-dir"></span>
  </div>
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

  <!-- Score submission + rank -->
  <div class="submit-card">
    <div class="submit-loading" id="submit-loading">
      <div class="loading-spinner-sm"></div>
      Saving score…
    </div>
    <div class="submit-success" id="submit-success">
      <p class="rank-label">90-day leaderboard rank</p>
      <span class="rank-num" id="rank-num">#?</span>
      <p class="rank-sub">among all scored games this season</p>
      <a href="/leaderboard/" class="rank-lb-link">View Full Leaderboard →</a>
    </div>
    <p class="submit-error" id="submit-error"></p>
  </div>

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

  <div class="end-actions">
    <a href="/" class="btn-green">Play Again</a>
    <a href="/leaderboard/" class="btn-outline">Leaderboard →</a>
  </div>
</div>

<!-- ════════════════ LIGHTBOX ════════════════ -->
<div id="lightbox">
  <div class="lightbox-close" onclick="closeLightbox()">✕</div>
  <img id="lb-img" src="" alt="">
  <div class="lightbox-caption" id="lb-caption"></div>
</div>

<script>
const photos = {game_data};

// ── Supabase ──────────────────────────────────────────────
const {{ createClient }} = supabase;
const sb = createClient('{SUPABASE_URL}', '{SUPABASE_ANON_KEY}');

let currentUser      = null;
let currentProfile   = null;
let isEditingProfile = false;

// ── Auth state listener ───────────────────────────────────
// INITIAL_SESSION fires exactly once on page load (session or null).
// This handles both returning users (session in localStorage) and
// the OAuth callback redirect (session from URL hash/code).
// No separate getSession() call needed — no race condition.
sb.auth.onAuthStateChange(async (event, session) => {{
  if (event === 'INITIAL_SESSION') {{
    if (session) {{
      currentUser = session.user;
      await loadProfile();
    }} else {{
      showScreen('screen-auth');
    }}
  }} else if (event === 'SIGNED_OUT') {{
    currentUser = null;
    currentProfile = null;
    showScreen('screen-auth');
  }}
}});

async function loadProfile() {{
  const {{ data }} = await sb
    .from('profiles')
    .select('trail_name, pct_year, about')
    .eq('id', currentUser.id)
    .maybeSingle();
  if (data) {{
    currentProfile = data;
    const greetEl = document.getElementById('greeting-name');
    greetEl.textContent = data.trail_name;
    greetEl.href = `/hiker/?id=${{currentUser.id}}`;
    prepareNextGame();
    showScreen('screen-start');
  }} else {{
    showScreen('screen-signup');
  }}
}}

async function signInWithGoogle() {{
  const btn = document.getElementById('btn-google');
  btn.disabled = true;
  btn.querySelector('svg').style.display = 'none';
  btn.childNodes[btn.childNodes.length - 1].textContent = ' Redirecting…';
  await sb.auth.signInWithOAuth({{
    provider: 'google',
    options: {{ redirectTo: 'https://pct-geoguesser.pages.dev/game/' }},
  }});
}}

async function saveProfile() {{
  const trailName = document.getElementById('trail-name-input').value.trim();
  const pctYear   = document.getElementById('pct-year-input').value.trim();
  const about     = document.getElementById('about-input').value.trim();
  const errEl     = document.getElementById('signup-error');
  const btn       = document.getElementById('btn-save-profile');
  errEl.textContent = '';
  if (!trailName) {{ errEl.textContent = 'Trail name is required.'; return; }}
  if (!pctYear)   {{ errEl.textContent = 'PCT year is required.';   return; }}
  btn.disabled = true;
  btn.textContent = 'Saving…';
  const hintEl = document.getElementById('save-slow-hint');
  hintEl.style.display = 'none';
  const slowTimer = setTimeout(() => {{
    hintEl.style.display = 'block';
    btn.textContent = 'Still saving…';
  }}, 5000);
  const {{ error }} = await sb.from('profiles').upsert({{
    id:         currentUser.id,
    trail_name: trailName,
    pct_year:   pctYear,
    about:      about || null,
  }});
  clearTimeout(slowTimer);
  hintEl.style.display = 'none';
  if (error) {{
    errEl.textContent = 'Error saving profile. Please try again.';
    btn.disabled = false;
    btn.textContent = isEditingProfile ? 'Save Changes' : 'Save and Play →';
    return;
  }}
  currentProfile = {{ trail_name: trailName, pct_year: pctYear, about: about || null }};
  const greetEl = document.getElementById('greeting-name');
  greetEl.textContent = trailName;
  greetEl.href = `/hiker/?id=${{currentUser.id}}`;
  // Reset signup screen back to "new user" state
  document.getElementById('signup-subtitle').textContent = 'One-time setup — your name and year appear on the leaderboard.';
  document.getElementById('signup-cancel').style.display = 'none';
  btn.textContent = 'Save and Play →';
  isEditingProfile = false;
  prepareNextGame();
  showScreen('screen-start');
}}

function showEditProfile() {{
  isEditingProfile = true;
  document.getElementById('trail-name-input').value = currentProfile?.trail_name || '';
  document.getElementById('pct-year-input').value   = currentProfile?.pct_year   || '';
  document.getElementById('about-input').value      = currentProfile?.about      || '';
  updateAboutCount();
  document.getElementById('signup-error').textContent = '';
  document.getElementById('signup-subtitle').textContent = 'Update your hiker profile.';
  document.getElementById('btn-save-profile').textContent = 'Save Changes';
  document.getElementById('btn-save-profile').disabled = false;
  document.getElementById('signup-cancel').style.display = 'block';
  showScreen('screen-signup');
}}

function cancelEditProfile() {{
  isEditingProfile = false;
  document.getElementById('signup-subtitle').textContent = 'One-time setup — your name and year appear on the leaderboard.';
  document.getElementById('btn-save-profile').textContent = 'Save and Play →';
  document.getElementById('signup-cancel').style.display = 'none';
  showScreen('screen-start');
}}

function updateAboutCount() {{
  const n = document.getElementById('about-input').value.length;
  document.getElementById('about-char-count').textContent = `(${{n}}/500)`;
}}

async function signOut() {{
  await sb.auth.signOut();
  // onAuthStateChange fires SIGNED_OUT → UI reset handled there
}}

// ── Score submission ──────────────────────────────────────
async function submitGameScore() {{
  const loadEl    = document.getElementById('submit-loading');
  const successEl = document.getElementById('submit-success');
  const errorEl   = document.getElementById('submit-error');
  loadEl.style.display    = 'flex';
  successEl.style.display = 'none';
  errorEl.style.display   = 'none';

  // Admin / test account — show a note but don't write to the leaderboard
  if (currentUser.email === 'curtisesjunk@gmail.com') {{
    loadEl.innerHTML = '<span style="color:var(--muted);font-size:13px">Test account — score not recorded.</span>';
    return;
  }}

  const totalScore   = scores.reduce((a, b) => a + b, 0);
  const perfectCount = scores.filter(s => s === 0).length;
  const guessPayload = gamePhotos.map((p, i) => ({{
    photo_id:     p.id,
    true_mile:    parseFloat(p.mile),
    guessed_mile: guesses[i],          // null if timed out
    score:        scores[i],
    timed_out:    guesses[i] === null,
  }}));

  const {{ error }} = await sb.rpc('submit_game', {{
    p_user_id:       currentUser.id,
    p_total_score:   totalScore,
    p_perfect_count: perfectCount,
    p_guesses:       guessPayload,
  }});

  loadEl.style.display = 'none';

  if (error) {{
    errorEl.textContent = error.message.includes('Rate limit')
      ? 'Please wait a few minutes between scored games.'
      : `Could not save score: ${{error.message}}`;
    errorEl.style.display = 'block';
    return;
  }}

  // Rank = count of games with a lower score in the last 90 days, + 1
  const ago90 = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString();
  const {{ count }} = await sb
    .from('game_sessions')
    .select('*', {{ count: 'exact', head: true }})
    .lt('total_score', totalScore)
    .gte('played_at', ago90);
  document.getElementById('rank-num').textContent = `#${{(count ?? 0) + 1}}`;
  successEl.style.display = 'flex';
}}

// ── Config ────────────────────────────────────────────────
const TIMER_SEC          = 30;
const FULL_CREDIT        = 3;
const GAME_SIZE          = 10;
const NO_ANSWER_PENALTY  = 1327.5;

// ── State ─────────────────────────────────────────────────
let gamePhotos = [], currentIdx = 0;
let scores = [], guesses = [];
let timerHandle = null, timeLeft = TIMER_SEC;

// ── Image preloading ──────────────────────────────────────
const _preloadCache = {{}};
function preload(url) {{
  if (!_preloadCache[url]) {{
    const img = new Image();
    img.src = url;
    _preloadCache[url] = img;
  }}
}}

function prepareNextGame() {{
  gamePhotos = selectGamePhotos();
  gamePhotos.forEach(p => preload(p.url));
}}

// ── Slider thumb: tri-colour gradient dot ─────────────────
const _SECTION_COLORS = [
  {{ start:    0,   end:  702.1, rgb: [200,169,110] }},
  {{ start:  702.1, end: 1092.3, rgb: [216,216,216] }},
  {{ start: 1092.3, end: 1692.0, rgb: [ 42,176, 98] }},
  {{ start: 1692.0, end: 2147.0, rgb: [  0,128,128] }},
  {{ start: 2147.0, end: 2655.5, rgb: [ 29, 80, 46] }},
];

function _lerp(c0, c1, t) {{ return c0.map((v, i) => Math.round(v + (c1[i] - v) * t)); }}
function _rgb(c)           {{ return `rgb(${{c[0]}},${{c[1]}},${{c[2]}})`; }}

function updateThumbColors(mile) {{
  let si = 0;
  while (si < _SECTION_COLORS.length - 1 && mile >= _SECTION_COLORS[si + 1].start) si++;
  const sec = _SECTION_COLORS[si];
  const t = (mile - sec.start) / (sec.end - sec.start);
  const center       = sec.rgb;
  const leftNeighbor  = si > 0                            ? _SECTION_COLORS[si - 1].rgb : center;
  const rightNeighbor = si < _SECTION_COLORS.length - 1  ? _SECTION_COLORS[si + 1].rgb : center;
  const leftEdge  = _lerp(leftNeighbor,  center, t);
  const rightEdge = _lerp(rightNeighbor, center, 1 - t);
  const sl = document.getElementById('trail-slider');
  sl.style.setProperty('--thumb-left',   _rgb(leftEdge));
  sl.style.setProperty('--thumb-center', _rgb(center));
  sl.style.setProperty('--thumb-right',  _rgb(rightEdge));
  sl.style.setProperty('--thumb-glow',   `rgba(${{center[0]}},${{center[1]}},${{center[2]}},.4)`);
}}

// ── Screens ───────────────────────────────────────────────
function showScreen(id) {{
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}}

// ── Photo selection: 2 random photos from each PCT section ─
const _PCT_SECTIONS = [
  'Southern California', 'The Sierra',
  'Northern California', 'Oregon', 'Washington',
];
const _PER_SECTION = 2;

function selectGamePhotos() {{
  const selected = [];
  for (const sec of _PCT_SECTIONS) {{
    const pool = photos.filter(p => p.section === sec).sort(() => Math.random() - .5);
    selected.push(...pool.slice(0, Math.min(_PER_SECTION, pool.length)));
  }}
  return selected.sort(() => Math.random() - .5);
}}

// ── Scoring ───────────────────────────────────────────────
function calcScore(guess, trueMile) {{
  return Math.abs(guess - trueMile) <= FULL_CREDIT ? 0 : Math.round(Math.abs(guess - trueMile));
}}

function getVerdictInfo(guess, trueMile) {{
  const diff = guess - trueMile;
  if (Math.abs(diff) <= FULL_CREDIT) return {{ text: 'Spot On! 🎯',                        cls: 'spoton' }};
  if (diff > 0)                      return {{ text: `${{fmt(diff)}} Miles North`,           cls: 'north'  }};
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
  currentIdx = 0; scores = []; guesses = [];
  showGuessScreen();
}}

function showGuessScreen() {{
  const p = gamePhotos[currentIdx];
  document.getElementById('g-cur').textContent    = currentIdx + 1;
  document.getElementById('g-tot').textContent    = gamePhotos.length;
  document.getElementById('g-photo').src          = p.url;
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
  document.getElementById('r-photo').src          = p.url;
  document.getElementById('r-mile').textContent    = `Mile ${{p.mile}}`;
  document.getElementById('r-section').textContent = p.section;
  document.getElementById('r-date').textContent    = p.date;
  document.getElementById('r-dir').textContent     = p.direction;
  document.getElementById('r-true-mile').textContent  = fmt(trueMile);
  document.getElementById('r-your-guess').textContent = timedOut ? '—' : fmt(guess);
  const stVerdict = document.getElementById('st-verdict');
  if (timedOut) {{
    stVerdict.textContent = 'Timed out';
    stVerdict.className   = 'rsc-verdict timeout';
  }} else {{
    const v = getVerdictInfo(guess, trueMile);
    stVerdict.textContent = v.text;
    stVerdict.className   = 'rsc-verdict ' + v.cls;
  }}
  const stRound = document.getElementById('st-round');
  if (score === 0) {{
    stRound.textContent = '0  🎯';
    stRound.className   = 'rsc-score-val perfect';
  }} else {{
    stRound.textContent = `${{fmt(score)}} mi`;
    stRound.className   = 'rsc-score-val';
  }}
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
  document.getElementById('final-avg').textContent =
    `On average, you were ${{fmt(avg)}} miles off.`;

  const tbody = document.getElementById('end-tbody');
  tbody.innerHTML = '';
  gamePhotos.forEach((p, i) => {{
    const guess    = guesses[i];
    const score    = scores[i];
    const trueMile = parseFloat(p.mile);
    const tr       = document.createElement('tr');

    const tdThumb = document.createElement('td');
    tdThumb.className = 'td-thumb';
    tdThumb.innerHTML = `<img class="et-thumb" src="${{p.url}}" alt=""
      onclick="openLightbox('${{p.url}}', 'Mile ${{p.mile}} · ${{p.section}} · ${{p.direction}}')">`;

    const tdGuess = document.createElement('td');
    if (guess === null) {{
      tdGuess.className   = 'td-guess no-answer';
      tdGuess.textContent = 'timed out';
    }} else {{
      tdGuess.className   = 'td-guess';
      tdGuess.textContent = fmt(guess);
    }}

    const tdMile = document.createElement('td');
    tdMile.className   = 'td-mile';
    tdMile.textContent = fmt(trueMile);

    const tdScore = document.createElement('td');
    tdScore.className   = 'td-score ' + (score === 0 ? 'perfect' : 'off');
    tdScore.textContent = score === 0 ? '✓ 0' : fmt(score);

    tr.append(tdThumb, tdMile, tdGuess, tdScore);
    tbody.appendChild(tr);
  }});

  showScreen('screen-end');

  // IMPORTANT: submitGameScore() must capture guessPayload BEFORE prepareNextGame()
  // overwrites gamePhotos. submitGameScore builds the payload synchronously (before
  // its first await), so calling it first is safe even though it's async.
  submitGameScore();

  // Preload next game's photos while user reads results (safe to overwrite now)
  prepareNextGame();
}}

// ── Lightbox ──────────────────────────────────────────────
function openLightbox(url, caption) {{
  document.getElementById('lb-img').src             = url;
  document.getElementById('lb-caption').textContent = caption;
  document.getElementById('lightbox').classList.add('open');
}}
function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('open');
  document.getElementById('lb-img').src = '';
}}
document.getElementById('lightbox').addEventListener('click', e => {{
  if (e.target === document.getElementById('lightbox')) closeLightbox();
}});

// ── Event listeners ───────────────────────────────────────
document.getElementById('mile-input').addEventListener('keydown', e => {{
  if (e.key === 'Enter') submitGuess();
}});

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

// ── Pinch-to-zoom + pan ───────────────────────────────────
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
      startRect  = frameEl.getBoundingClientRect();
      e.preventDefault();
    }} else if (e.touches.length === 1 && scale > 1) {{
      lastX = e.touches[0].clientX;
      lastY = e.touches[0].clientY;
    }}
  }}, {{ passive: false }});

  frameEl.addEventListener('touchmove', e => {{
    if (e.touches.length === 2) {{
      const newScale = clamp(startScale * touchDist(e.touches) / startDist, 1, 6);
      const focalX = (e.touches[0].clientX + e.touches[1].clientX) / 2
                   - (startRect.left + startRect.width  / 2);
      const focalY = (e.touches[0].clientY + e.touches[1].clientY) / 2
                   - (startRect.top  + startRect.height / 2);
      const ratio = newScale / scale;
      panX  = focalX + (panX - focalX) * ratio;
      panY  = focalY + (panY - focalY) * ratio;
      scale = newScale;
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

makePinchZoom(
  document.querySelector('#screen-guess .photo-frame'),
  document.getElementById('g-photo'),
  'resetPhotoZoom'
);
makePinchZoom(
  document.querySelector('#screen-result .result-photo-wrap'),
  document.getElementById('r-photo'),
  'resetResultZoom'
);

document.addEventListener('touchmove', e => {{
  if (e.touches.length > 1) {{
    const guessFrame  = document.querySelector('#screen-guess .photo-frame');
    const resultFrame = document.querySelector('#screen-result .result-photo-wrap');
    if (!guessFrame.contains(e.target) && !resultFrame.contains(e.target)) {{
      e.preventDefault();
    }}
  }}
}}, {{ passive: false }});

// ── Kick-off ──────────────────────────────────────────────
// Auth handled by onAuthStateChange above — INITIAL_SESSION fires on load.
</script>
</body>
</html>
"""

with open(OUT_PATH, "w") as f:
    f.write(html)

print(f"Built {OUT_PATH}")
print(f"  {len(v2_photos)} v2-scored photos available")
