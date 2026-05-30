# ──────────────────────────────────────────────────────────────────────────────
# build.py  —  PCT GeoGuesser  (landing page)
#
# Generates a single self-contained index.html for the landing page at /.
# No external data dependencies — purely static HTML/CSS, no photos.csv needed.
#
# To rebuild after editing:
#   python3 app-landing/build.py
#
# To deploy:
#   bash build.sh
#   npx wrangler pages deploy deploy/ --project-name=pct-geoguesser
# ──────────────────────────────────────────────────────────────────────────────

import os
HERE          = os.path.dirname(os.path.abspath(__file__))
OUT_PATH      = os.path.join(HERE, "index.html")
MISC_BASE_URL = "https://pct-geoguesser.pages.dev/misc"

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
<meta name="description" content="How well do you know the Pacific Crest Trail? Play PCT GeoGuesser.">
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
  --pct-green: #1D502E;   /* forest green  — scored game button, accents */
  --pct-teal:  #008080;   /* teal/dark cyan — practice button, links     */
  --pct-white: #FFFFFF;
}}

body {{
  font-family: 'Futura', 'Futura PT', 'Open Sans', Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}}

/* ── Landing wrapper ──────────────────────────────────── */
.landing {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  padding: 24px 20px;
  text-align: center;
  width: 100%;
  max-width: 640px;
}}

/* ── Logo ─────────────────────────────────────────────── */
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

/* ── Heading ──────────────────────────────────────────── */
h1 {{
  font-size: clamp(26px, 8.5vw, 56px);
  font-weight: 800; line-height: 1.1;
  color: var(--pct-white);
  text-shadow: 0 0 30px rgba(0,128,128,.4);
  white-space: nowrap;   /* always one line */
}}
h1 span {{ color: var(--pct-teal); }}

.start-sub {{
  color: var(--muted); font-size: 14px; max-width: 360px; line-height: 1.5;
}}

/* ── Rules card ───────────────────────────────────────── */
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

/* ── Two CTA buttons ──────────────────────────────────── */
.start-buttons {{
  display: flex;
  gap: 12px;
  max-width: 400px;
  width: 100%;
}}
.btn-cta {{
  flex: 1;
  border: none;
  border-radius: 10px;
  padding: 13px 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: filter .15s, transform .1s;
  letter-spacing: .01em;
  color: var(--pct-white);
  text-align: center;
  line-height: 1.3;
}}
/* Practice — PCT teal; Scored — PCT green */
.btn-practice {{ background: var(--pct-teal); }}
.btn-scored   {{ background: var(--pct-green); }}
.btn-cta:hover  {{ filter: brightness(1.25); transform: translateY(-1px); }}
.btn-cta:active {{ transform: translateY(0); }}

/* Stack vertically on very narrow screens */
@media (max-width: 380px) {{
  .start-buttons {{ flex-direction: column; }}
  .btn-cta {{ width: 100%; }}
}}

/* ── About link ───────────────────────────────────────── */
.about-link {{ font-size: 12px; color: var(--muted); text-align: center; }}

/* ── Mobile: larger logos ─────────────────────────────── */
@media (max-width: 640px) {{
  .logo-box {{ padding: 18px; gap: 24px; }}
  .logo-old {{ height: 140px; }}
  .logo-new {{ height: 126px; }}
}}

/* ── Desktop: scale everything up ────────────────────── */
@media (min-width: 900px) {{
  .landing {{ gap: 26px; }}
  .logo-old {{ height: 117px; }}
  .logo-new {{ height: 106px; }}
  .start-sub {{ font-size: 18px; max-width: 520px; }}
  .rules-card {{ max-width: 580px; padding: 22px 26px; }}
  .rules-card h3 {{ font-size: 12px; margin-bottom: 14px; }}
  .rules-card li {{ font-size: 16px; }}
  .start-buttons {{ max-width: 580px; gap: 16px; }}
  .btn-cta {{ font-size: 18px; padding: 15px 16px; }}
}}
</style>
</head>
<body>

<div class="landing">

  <!-- Logo -->
  <div class="logo-pair">
    <div class="logo-box">
      <img src="{MISC_BASE_URL}/pct-orig-logo.webp" class="logo-old" alt="PCT original logo">
      <img src="{MISC_BASE_URL}/pct-new-logo.webp"  class="logo-new" alt="PCT shield logo">
    </div>
  </div>

  <!-- Title -->
  <h1>PCT <span>GeoGuesser</span></h1>
  <p class="start-sub">How well do you know the Pacific Crest Trail?</p>

  <!-- Rules card -->
  <div class="rules-card">
    <h3>How to Play</h3>
    <ul>
      <li>You'll see 10 photos taken somewhere along the PCT</li>
      <li><span>Enter the PCT (NoBo) mile you think matches the location (<a href="https://pcta.maps.arcgis.com/apps/instant/sidebar/index.html?appid=3b1817932adf42009f30b6b38828212e" target="_blank" rel="noopener">see PCTA mile markers</a>)</span></li>
      <li>You'll have <strong>45 seconds</strong> to guess</li>
    </ul>
    <h3>Scoring (top score wins)</h3>
    <ul>
      <li>The closer your guesses are to the correct mile, the better your score.</li>
      <li>Within <strong>3 miles</strong> = perfect score</li>
      <li>Top score possible is <strong>2,655.8</strong></li>
    </ul>
    <h3>Tips</h3>
    <ul>
      <li>Photos can come from anywhere along the full trail.</li>
      <li>Pay attention to the date &amp; hiking direction. Not every photo was taken during summer.</li>
    </ul>
  </div>

  <!-- CTA buttons -->
  <div class="start-buttons">
    <a href="/practice/" class="btn-cta btn-practice">Practice Game →</a>
    <a href="/game/"     class="btn-cta btn-scored">Scored Game →</a>
  </div>

  <p class="about-link"><a href="/about/" style="color:var(--muted);text-decoration:none;">About PCT GeoGuesser</a></p>

</div>

</body>
</html>
"""

with open(OUT_PATH, "w") as f:
    f.write(html)

print(f"Built {OUT_PATH}")
