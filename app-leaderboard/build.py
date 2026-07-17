# ──────────────────────────────────────────────────────────────────────────────
# build.py  —  PCT GeoGuesser  (leaderboard)
#
# Generates a single leaderboard page:
#   app-leaderboard/index.html  →  deployed at /leaderboard/
#
# Default view: All-Time (highest score per player, ever).
# 90-Day tab: shown only when the admin enables it via Site Settings.
#   The page fetches `site_settings` where key='show_rolling_leaderboard' on
#   load. If value='true', a 90-Day tab appears alongside All-Time. Otherwise
#   only All-Time is shown, with no tab bar.
#
# Row highlighting: init() calls sb.auth.getSession() to get the logged-in
#   player's user_id. When building table rows, any row whose user_id matches
#   gets a .lb-row-me class (teal tint + left accent border). No-op if not
#   signed in. Applies to both All-Time and 90-Day tabs.
#
# To rebuild:
#   python3 app-leaderboard/build.py
#
# To deploy:
#   bash build.sh
# ──────────────────────────────────────────────────────────────────────────────

import os
sys = __import__('sys')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'misc'))
from supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY

HERE         = os.path.dirname(os.path.abspath(__file__))
MISC_BASE_URL = "https://pct-geoguesser.economicurtis.com/misc"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>PCT GeoGuesser — Leaderboard</title>
<meta name="description" content="PCT GeoGuesser leaderboard — see the top scores on the Pacific Crest Trail guessing game.">
<!-- Open Graph / social preview -->
<meta property="og:type"        content="website">
<meta property="og:url"         content="https://pct-geoguesser.economicurtis.com/leaderboard/">
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
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>
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
  --pct-white: #FFFFFF;
  /* ── Font preference (overridden at runtime if site_settings primary_font
        is set to 'open-sans'). Default: Futura stack. ── */
  --font-primary: 'Futura', 'Futura PT', 'Open Sans', Arial, sans-serif;
}}

body {{
  font-family: var(--font-primary);
  background: var(--bg);
  color: var(--text);
  min-height: 100dvh;
}}

.top-nav {{
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  max-width: 760px;
  margin: 0 auto;
  width: 100%;
}}
.back-link {{
  color: var(--pct-teal);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}}
.back-link:hover {{ text-decoration: underline; }}

.page {{
  max-width: 760px;
  margin: 0 auto;
  padding: 0 16px 48px;
}}

.page-header {{
  padding: 28px 0 16px;
  text-align: center;
}}
.page-header h1 {{
  font-size: clamp(22px, 5vw, 36px);
  font-weight: 800;
  color: var(--pct-white);
}}

/* Tab bar — hidden by default, shown only when 90-day is enabled */
.tab-bar {{
  display: flex;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 24px;
}}
.tab {{
  flex: 1;
  padding: 10px 16px;
  text-align: center;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  color: var(--muted);
  background: var(--surface);
  border: none;
  transition: background .15s, color .15s;
}}
.tab:hover:not(.tab-active) {{ background: var(--surface2); color: var(--text); }}
.tab.tab-active {{
  background: var(--pct-green);
  color: var(--pct-white);
  cursor: default;
}}

.state-msg {{
  text-align: center;
  padding: 60px 20px;
  color: var(--muted);
  font-size: 15px;
}}
.state-msg .spinner {{
  display: inline-block;
  width: 28px; height: 28px;
  border: 3px solid var(--border);
  border-top-color: var(--pct-teal);
  border-radius: 50%;
  animation: spin .8s linear infinite;
  margin-bottom: 16px;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}

.lb-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}}
.lb-table th {{
  text-align: left;
  padding: 8px 12px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
}}
.lb-table td {{
  padding: 12px 12px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}}
.lb-table tr:last-child td {{ border-bottom: none; }}
.lb-table tbody tr:hover {{ background: var(--surface2); }}
/* Highlight the logged-in player's own row */
.lb-row-me {{
  background: rgba(0, 128, 128, 0.10);
  border-left: 3px solid var(--pct-teal);
}}
.lb-row-me:hover {{ background: rgba(0, 128, 128, 0.18); }}

.rank-cell {{
  font-size: 16px;
  text-align: center;
  width: 44px;
  color: var(--muted);
  font-weight: 700;
}}
.rank-medal {{ font-size: 20px; }}
.name-cell {{ min-width: 140px; }}
.hiker-link {{
  color: var(--pct-teal);
  font-weight: 700;
  text-decoration: none;
  font-size: 15px;
}}
.hiker-link:hover {{ text-decoration: underline; color: #5fd4d4; }}
.pct-year {{
  display: block;
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}}
.score-cell {{
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
}}
.perf-cell {{
  color: var(--muted);
  font-size: 13px;
  white-space: nowrap;
}}
.perf-cell.all-perfect {{
  color: var(--pct-teal);
  font-weight: 700;
}}
.window-note {{
  text-align: center;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 16px;
}}

@media (min-width: 600px) {{
  .lb-table {{ font-size: 15px; }}
  .lb-table th {{ font-size: 12px; padding: 10px 16px; }}
  .lb-table td {{ padding: 14px 16px; }}
  .hiker-link {{ font-size: 16px; }}
}}
</style>
<script>
/* ── Font preference ────────────────────────────────────────────────────────
   Applies the site's primary_font setting from Supabase site_settings.
   localStorage key 'pct_font' is read synchronously so the correct font
   is set before first paint (no flash). A background fetch then updates
   the cache if the setting has changed in the admin panel.
   Values: 'futura' (default) | 'open-sans'  ── */
(function() {{
  var STACKS = {{
    'futura':    "'Futura', 'Futura PT', 'Open Sans', Arial, sans-serif",
    'open-sans': "'Open Sans', Arial, sans-serif"
  }};
  var cached = localStorage.getItem('pct_font');
  if (cached && STACKS[cached]) {{
    document.documentElement.style.setProperty('--font-primary', STACKS[cached]);
  }}
  fetch('{SUPABASE_URL}/rest/v1/site_settings?select=key,value&key=eq.primary_font', {{
    headers: {{ 'apikey': '{SUPABASE_ANON_KEY}', 'Authorization': 'Bearer {SUPABASE_ANON_KEY}' }}
  }}).then(function(r) {{ return r.json(); }}).then(function(rows) {{
    if (!rows || !rows.length) return;
    var val = rows[0].value;
    if (!STACKS[val]) return;
    localStorage.setItem('pct_font', val);
    document.documentElement.style.setProperty('--font-primary', STACKS[val]);
  }}).catch(function() {{}});
}})();
</script>
</head>
<body>

<nav style="border-bottom:1px solid var(--border)">
  <div class="top-nav">
    <a href="/" class="back-link">← PCT GeoGuesser</a>
  </div>
</nav>

<div class="page">
  <div class="page-header">
    <h1 id="lb-title">Leaderboard</h1>
  </div>

  <!-- Tab bar: hidden until 90-day setting is confirmed enabled -->
  <div class="tab-bar" id="tab-bar" style="display:none">
    <button class="tab" id="tab-alltime" onclick="switchView('alltime')">All-Time</button>
    <button class="tab" id="tab-rolling" onclick="switchView('rolling')">90-Day</button>
  </div>

  <p class="window-note" id="window-note"></p>

  <div id="state-loading" class="state-msg">
    <div class="spinner"></div><br>Loading scores…
  </div>
  <div id="state-empty" class="state-msg" hidden>No scores yet — be the first!</div>
  <div id="state-error" class="state-msg" hidden>
    <div style="font-size:32px;margin-bottom:12px">⛺</div>
    <div id="error-msg" style="font-size:16px;font-weight:700;color:var(--text);margin-bottom:8px">Leaderboard temporarily unavailable</div>
    <div style="margin-bottom:20px">The server may be resting — try again in a minute.</div>
    <a href="https://forms.gle/LSnZgRYr5yHG3AhR8" target="_blank" rel="noopener"
       style="color:var(--pct-teal);font-size:13px;text-decoration:underline">Report an issue ↗</a>
  </div>

  <table id="lb-table" class="lb-table" hidden>
    <thead>
      <tr>
        <th style="text-align:center">#</th>
        <th>Trail Name</th>
        <th>Best Score</th>
        <th>Perfects</th>
      </tr>
    </thead>
    <tbody id="lb-body"></tbody>
  </table>
</div>

<script>
const sb = supabase.createClient('{SUPABASE_URL}', '{SUPABASE_ANON_KEY}');
const MEDALS = ['🥇','🥈','🥉'];

// Current view: 'alltime' (default) or 'rolling'
let currentView = 'alltime';
let rollingEnabled = false;
// Logged-in user's ID — set in init(); null if not signed in
let currentUserId = null;

function showState(id) {{
  ['state-loading','state-empty','state-error','lb-table']
    .forEach(s => document.getElementById(s).hidden = (s !== id));
}}

function switchView(view) {{
  currentView = view;
  document.getElementById('tab-alltime').classList.toggle('tab-active', view === 'alltime');
  document.getElementById('tab-rolling').classList.toggle('tab-active', view === 'rolling');
  loadScores();
}}

async function loadScores() {{
  showState('state-loading');
  try {{
    let query = sb
      .from('game_sessions')
      .select('user_id, total_score, perfect_count, photo_count, played_at, profiles(id, trail_name, pct_year)')
      .order('total_score', {{ ascending: false }})
      .limit(500);

    if (currentView === 'rolling') {{
      const ago90 = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString();
      query = query.gte('played_at', ago90);
    }}

    const {{ data, error }} = await query;
    if (error) throw error;

    // Keep only the best score per user (already sorted DESC, first hit = best)
    const seen = new Set();
    const rows = [];
    for (const row of (data ?? [])) {{
      if (row.profiles && !seen.has(row.user_id)) {{
        seen.add(row.user_id);
        rows.push(row);
        if (rows.length >= 100) break;
      }}
    }}

    if (rows.length === 0) {{ showState('state-empty'); return; }}

    document.getElementById('window-note').textContent = currentView === 'rolling'
      ? 'Highest score per player in the last 90 days · max 2655.8 pts'
      : 'Highest score per player, all time · max 2655.8 pts';

    const tbody = document.getElementById('lb-body');
    tbody.innerHTML = '';
    rows.forEach((row, i) => {{
      const rank      = i + 1;
      const profileId = row.profiles.id;
      const name      = row.profiles.trail_name || 'Anonymous';
      const pctYear   = row.profiles.pct_year   || '';
      const score     = Number(row.total_score).toFixed(1);
      const perfects  = row.perfect_count ?? 0;
      const total     = row.photo_count   ?? 10;
      const allPerf   = perfects === total;

      const rankHtml = rank <= 3
        ? `<span class="rank-medal">${{MEDALS[rank-1]}}</span>`
        : `${{rank}}`;
      const yearHtml = pctYear
        ? `<span class="pct-year">PCT ${{pctYear}}</span>`
        : '';

      const tr = document.createElement('tr');
      // Highlight the current player's own row
      if (currentUserId && row.user_id === currentUserId) {{
        tr.classList.add('lb-row-me');
      }}
      tr.innerHTML = `
        <td class="rank-cell">${{rankHtml}}</td>
        <td class="name-cell">
          <a href="/hiker/?id=${{profileId}}" class="hiker-link">${{name}}</a>
          ${{yearHtml}}
        </td>
        <td class="score-cell">${{score}} pts</td>
        <td class="perf-cell${{allPerf ? ' all-perfect' : ''}}">${{perfects}}/${{total}}</td>
      `;
      tbody.appendChild(tr);
    }});

    showState('lb-table');
  }} catch (err) {{
    // Network/fetch failures show a friendly unavailable message; leave the
    // default error-msg text in place (set in HTML) rather than surfacing a
    // raw "TypeError: Failed to fetch" to the player.
    const isNetworkErr = !err.message || err.message.toLowerCase().includes('fetch') || err.message.toLowerCase().includes('network');
    if (!isNetworkErr) {{
      document.getElementById('error-msg').textContent = err.message;
    }}
    showState('state-error');
  }}
}}

async function init() {{
  // Identify the logged-in player (if any) so their row can be highlighted
  try {{
    const {{ data: {{ session }} }} = await sb.auth.getSession();
    currentUserId = session?.user?.id ?? null;
  }} catch (_) {{}}

  // Check admin setting: show_rolling_leaderboard
  try {{
    const {{ data }} = await sb
      .from('site_settings')
      .select('value')
      .eq('key', 'show_rolling_leaderboard')
      .maybeSingle();
    rollingEnabled = data?.value === 'true';
  }} catch (_) {{
    rollingEnabled = false;
  }}

  if (rollingEnabled) {{
    document.getElementById('tab-bar').style.display = '';
    document.getElementById('lb-title').textContent = 'All-Time Leaderboard';
    document.getElementById('tab-alltime').classList.add('tab-active');
  }} else {{
    document.getElementById('lb-title').textContent = 'Leaderboard';
  }}

  currentView = 'alltime';
  loadScores();
}}

init();
</script>
</body>
</html>"""

out = os.path.join(HERE, 'index.html')
with open(out, 'w') as f:
    f.write(html)
print(f"Built {out}")
