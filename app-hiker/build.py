# ──────────────────────────────────────────────────────────────────────────────
# build.py  —  PCT GeoGuesser  (hiker profile page)
#
# Generates a single self-contained index.html deployed at /hiker/.
# The page reads ?id=<uuid> from the URL, fetches the player's profile
# and game history from Supabase, and displays their stats.
#
# URL format: https://pct-geoguesser.economicurtis.com/hiker/?id=<full-uuid>
# The leaderboard links to this page using the full Supabase profile UUID.
#
# To rebuild:
#   python3 app-hiker/build.py
#
# To deploy:
#   cp app-hiker/index.html deploy/hiker/index.html
#   npx wrangler pages deploy deploy/ --project-name=pct-geoguesser
# ──────────────────────────────────────────────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'misc'))
from supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY

HERE     = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "index.html")
MISC_BASE_URL = "https://pct-geoguesser.economicurtis.com/misc"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>PCT GeoGuesser — Hiker Profile</title>
<meta name="description" content="PCT GeoGuesser hiker profile and game history.">
<!-- Open Graph / social preview -->
<meta property="og:type"        content="website">
<meta property="og:url"         content="https://pct-geoguesser.economicurtis.com/hiker/">
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
<link rel="icon"             type="image/png" href="{MISC_BASE_URL}/pct-geoguesser-favicon.png">
<link rel="apple-touch-icon"                  href="{MISC_BASE_URL}/pct-geoguesser-favicon.png">
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
  --gold:      #f59e0b;
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

/* ── Top nav ─────────────────────────────────────────────── */
.top-nav-bar {{
  border-bottom: 1px solid var(--border);
}}
.top-nav {{
  padding: 14px 20px;
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
.nav-right {{
  display: flex;
  gap: 16px;
  align-items: center;
}}
.nav-right a {{
  color: var(--muted);
  text-decoration: none;
  font-size: 13px;
}}
.nav-right a:hover {{ color: var(--text); }}

/* ── Page ────────────────────────────────────────────────── */
.page {{
  max-width: 760px;
  margin: 0 auto;
  padding: 32px 20px 60px;
}}

/* ── State messages ──────────────────────────────────────── */
.state-msg {{
  text-align: center;
  padding: 80px 20px;
  color: var(--muted);
}}
.spinner {{
  display: inline-block;
  width: 32px; height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--pct-teal);
  border-radius: 50%;
  animation: spin .8s linear infinite;
  margin-bottom: 16px;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}

/* ── Profile card ────────────────────────────────────────── */
.profile-card {{
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 32px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--border);
}}
.profile-avatar {{
  width: 64px; height: 64px;
  border-radius: 50%;
  background: var(--pct-green); /* overridden by JS with user-specific color */
  display: flex; align-items: center; justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
  border: 2px solid var(--border);
}}
.profile-info {{
  flex: 1;
  min-width: 0;
}}
.profile-name {{
  font-size: clamp(22px, 5vw, 32px);
  font-weight: 800;
  color: var(--pct-teal);
  line-height: 1.1;
  margin-bottom: 4px;
}}
.profile-year {{
  font-size: 14px;
  color: var(--muted);
  margin-bottom: 10px;
}}
.profile-about {{
  font-size: 14px;
  color: var(--text);
  line-height: 1.6;
  opacity: .85;
}}

/* ── Hero score card ─────────────────────────────────────── */
.hero-card {{
  background: var(--surface);
  border: 1px solid var(--pct-teal);
  border-radius: 14px;
  padding: 24px 28px;
  text-align: center;
  margin-bottom: 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}}
.hero-score-label {{
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .12em;
  color: var(--muted);
}}
.hero-score {{
  font-size: clamp(52px, 12vw, 80px);
  font-weight: 800;
  line-height: 1;
  color: var(--pct-teal);
  font-variant-numeric: tabular-nums;
}}
.hero-score-max {{
  font-size: 14px;
  color: var(--muted);
  margin-top: -4px;
}}
.hero-callout {{
  font-size: clamp(14px, 3.5vw, 17px);
  font-weight: 600;
  color: var(--text);
  line-height: 1.4;
  max-width: 480px;
  margin-top: 4px;
}}
.hero-rankings {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 4px;
}}
.ranking-badge {{
  background: rgba(0,128,128,.15);
  border: 1px solid rgba(0,128,128,.4);
  color: var(--pct-teal);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
  padding: 4px 14px;
}}
.hero-support-stats {{
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 6px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  width: 100%;
}}
.support-stat {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}}
.support-stat-val   {{ font-size: 20px; font-weight: 800; color: var(--text); font-variant-numeric: tabular-nums; }}
.support-stat-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }}

/* ── Section heading ─────────────────────────────────────── */
.section-heading {{
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--pct-teal);
  margin-bottom: 12px;
}}

/* ── Games table ─────────────────────────────────────────── */
.table-wrap {{ overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; }}
.games-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}}
.games-table th {{
  padding: 8px 14px;
  text-align: left;
  font-size: 10px; text-transform: uppercase; letter-spacing: .08em;
  color: var(--muted); border-bottom: 1px solid var(--border);
  background: var(--surface); white-space: nowrap;
}}
.games-table td {{
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
  white-space: nowrap;
}}
.games-table tr:last-child td {{ border-bottom: none; }}
.games-table tbody tr:hover {{ background: var(--surface2); }}

.td-score {{
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}}
.td-score.best {{
  color: var(--pct-teal);
}}
.td-date   {{ color: var(--muted); font-size: 12px; }}
.td-perfs  {{ color: var(--muted); font-size: 13px; }}
.td-perfs.all-perfect {{ color: var(--pct-teal); font-weight: 700; }}
.best-badge {{
  display: inline-block;
  background: rgba(245,158,11,.15);
  border: 1px solid rgba(245,158,11,.4);
  color: var(--gold);
  border-radius: 5px;
  font-size: 10px; font-weight: 700; letter-spacing: .05em;
  padding: 2px 7px; margin-left: 6px;
  vertical-align: middle;
}}
.rank-badge {{
  display: inline-block;
  background: rgba(0,128,128,.15);
  border: 1px solid rgba(0,128,128,.4);
  color: var(--pct-teal);
  border-radius: 5px;
  font-size: 10px; font-weight: 700; letter-spacing: .05em;
  padding: 2px 7px; margin-left: 4px;
  vertical-align: middle;
}}

/* ── No games state ──────────────────────────────────────── */
.no-games {{
  padding: 32px;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
}}

/* ── Desktop ─────────────────────────────────────────────── */
@media (min-width: 600px) {{
  .profile-avatar {{ width: 80px; height: 80px; font-size: 36px; }}
  .stat-chip-val {{ font-size: 26px; }}
  .games-table {{ font-size: 14px; }}
  .games-table th {{ font-size: 11px; padding: 10px 16px; }}
  .games-table td {{ padding: 12px 16px; }}
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

<div class="top-nav-bar">
  <div class="top-nav">
    <a href="/" class="back-link">← PCT GeoGuesser</a>
    <div class="nav-right">
      <a href="/leaderboard/">Leaderboard</a>
      <a href="/game/">Play →</a>
    </div>
  </div>
</div>

<!-- Loading -->
<div id="state-loading" class="state-msg">
  <div class="spinner"></div><br>Loading profile…
</div>

<!-- Not found -->
<div id="state-notfound" class="state-msg" hidden>
  <p style="font-size:32px;margin-bottom:12px">🏔</p>
  <p>Hiker not found.</p>
  <p style="margin-top:8px"><a href="/leaderboard/" style="color:var(--pct-teal)">← Leaderboard</a></p>
</div>

<!-- Error -->
<div id="state-error" class="state-msg" hidden>
  <span id="error-msg" style="color:#dc2626">Something went wrong.</span>
</div>

<!-- Profile content -->
<div id="profile-content" class="page" hidden>

  <!-- Profile card -->
  <div class="profile-card">
    <div class="profile-avatar" id="profile-avatar">🏕</div>
    <div class="profile-info">
      <div class="profile-name"  id="profile-name">—</div>
      <div class="profile-year"  id="profile-year"></div>
      <div class="profile-about" id="profile-about"></div>
    </div>
  </div>

  <!-- Hero score card -->
  <div class="hero-card">
    <div class="hero-score-label">Best Score</div>
    <div class="hero-score" id="hero-score">—</div>
    <div class="hero-score-max" id="hero-score-max"></div>
    <div class="hero-callout" id="hero-callout"></div>
    <div class="hero-rankings" id="hero-rankings"></div>
    <div class="hero-support-stats" id="hero-support-stats">
      <div class="support-stat">
        <div class="support-stat-val" id="stat-games">—</div>
        <div class="support-stat-label">Games Played</div>
      </div>
      <div class="support-stat">
        <div class="support-stat-val" id="stat-avg">—</div>
        <div class="support-stat-label">Avg Score</div>
      </div>
      <div class="support-stat">
        <div class="support-stat-val" id="stat-perfects">—</div>
        <div class="support-stat-label">Total Perfects</div>
      </div>
    </div>
  </div>

  <!-- Game history -->
  <div class="section-heading">Game History</div>
  <div id="games-container"></div>

</div>

<script>
const sb = supabase.createClient('{SUPABASE_URL}', '{SUPABASE_ANON_KEY}');

function showState(id) {{
  ['state-loading','state-notfound','state-error','profile-content']
    .forEach(s => {{ document.getElementById(s).hidden = (s !== id); }});
}}

const MAX_SCORE = 2655.8;

function getCalloutText(name, bestScore) {{
  if (bestScore <= 0) return `No scores yet — time to hit the trail!`;
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
  return pick([
    `It's almost like ${{name}} walked over every inch of the PCT.`,
    `${{name}} may have built the whole PCT.`,
    `${{name}} knows the PCT better than marmots look chonky.`,
    `Pikas ask ${{name}} for directions.`,
    `${{name}} knows the PCT almost as much as they smell.`,
    `Okay, did ${{name}} hike the trail twice or something?`,
    `${{name}} is so one with the trail, bears need to carry a ${{name}}-canister.`,
    `${{name}} really knows the PCT — that's elite trail knowledge.`,
    `Wow, ${{name}} really knows the PCT.`,
    `The mayor of Idyllwild would like to give ${{name}} a tasty treat.`,
    `${{name}} knows the trail so well they pronounce "Seiad Valley" correctly.`,
    `Wow, ${{name}} knows their trail.`,
    `${{name}} knows their way around the trail pretty darn well.`,
    `Not bad, ${{name}}. The PCT recognizes one of its own.`,
    `The trail gods give ${{name}} a polite nod.`,
    `${{name}} is the legend every map wishes it had.`,
    `Every good map has a legend to show you how far you've gone. My legend is ${{name}}.`,
    `${{name}} has some serious PCT knowledge.`,
    `${{name}} knows enough to be dangerous near a resupply box.`,
    `${{name}} is getting to know the trail well!`,
    `Every guess is a step closer to knowing the PCT. Keep exploring!`,
  ]);
}}

async function load() {{
  const params = new URLSearchParams(window.location.search);
  const userId = params.get('id');

  if (!userId) {{ showState('state-notfound'); return; }}

  try {{
    const ago90str = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString();

    // Fetch profile, games, and leaderboard data in parallel
    const [profileRes, gamesRes, lb90Res, lbAllRes] = await Promise.all([
      sb.from('profiles')
        .select('id, trail_name, pct_year, about')
        .eq('id', userId)
        .maybeSingle(),
      sb.from('game_sessions')
        .select('id, total_score, perfect_count, photo_count, played_at')
        .eq('user_id', userId)
        .order('total_score', {{ ascending: false }}),
      // 90-day leaderboard for ranking
      sb.from('game_sessions')
        .select('user_id, total_score')
        .gte('played_at', ago90str)
        .order('total_score', {{ ascending: false }})
        .limit(500),
      // All-time leaderboard for ranking
      sb.from('game_sessions')
        .select('user_id, total_score')
        .order('total_score', {{ ascending: false }})
        .limit(500),
    ]);

    if (profileRes.error) throw profileRes.error;
    if (!profileRes.data) {{ showState('state-notfound'); return; }}

    const profile = profileRes.data;
    const games   = gamesRes.data || [];

    // Deduplicate leaderboard rows (best per user, first = best since sorted desc)
    function dedup(rows) {{
      const seen = new Set(), out = [];
      for (const r of (rows || [])) {{
        if (!seen.has(r.user_id)) {{ seen.add(r.user_id); out.push(r); }}
        if (out.length >= 100) break;
      }}
      return out;
    }}
    const lb90  = dedup(lb90Res.data);
    const lbAll = dedup(lbAllRes.data);
    const rank90  = lb90.findIndex(r  => r.user_id === userId) + 1;   // 0 = not in top 100
    const rankAll = lbAll.findIndex(r => r.user_id === userId) + 1;

    renderProfile(profile, games, rank90, rankAll);
    showState('profile-content');

  }} catch (err) {{
    document.getElementById('error-msg').textContent = err.message || 'Failed to load profile.';
    showState('state-error');
  }}
}}

function renderProfile(profile, games, rank90, rankAll) {{
  // Update page title
  const name = profile.trail_name || 'Anonymous Hiker';
  document.title = `${{name}} — PCT GeoGuesser`;

  // Profile card
  document.getElementById('profile-name').textContent = name;
  document.getElementById('profile-avatar').textContent       = getAvatarEmoji(profile.trail_name);
  document.getElementById('profile-avatar').style.background = getAvatarColor(profile.id);

  if (profile.pct_year) {{
    document.getElementById('profile-year').textContent = `PCT ${{profile.pct_year}}`;
  }}
  if (profile.about) {{
    document.getElementById('profile-about').textContent = profile.about;
  }}

  const n = games.length;
  document.getElementById('stat-games').textContent = n;

  if (n > 0) {{
    const bestScore = Math.max(...games.map(g => g.total_score));
    const avgScore  = games.reduce((s, g) => s + g.total_score, 0) / n;
    const totalPerf = games.reduce((s, g) => s + (g.perfect_count ?? 0), 0);

    // Hero card
    document.getElementById('hero-score').textContent     = bestScore.toFixed(1);
    document.getElementById('hero-score-max').textContent = `/ ${{MAX_SCORE}}`;
    document.getElementById('hero-callout').textContent   = getCalloutText(name, bestScore);

    // Ranking badges
    const rankingsEl = document.getElementById('hero-rankings');
    rankingsEl.innerHTML = '';
    if (rank90 > 0)  rankingsEl.innerHTML += `<span class="ranking-badge">#${{rank90}} · 90-Day Leaderboard</span>`;
    if (rankAll > 0) rankingsEl.innerHTML += `<span class="ranking-badge">#${{rankAll}} · All-Time Leaderboard</span>`;

    // Support stats
    document.getElementById('stat-avg').textContent      = avgScore.toFixed(1);
    document.getElementById('stat-perfects').textContent = totalPerf;

    // 90-day cutoff for best-badge logic
    const ago90 = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);

    // Build game history table
    const container = document.getElementById('games-container');
    const wrap = document.createElement('div');
    wrap.className = 'table-wrap';
    const table = document.createElement('table');
    table.className = 'games-table';
    table.innerHTML = `
      <thead>
        <tr>
          <th>Date</th>
          <th>Score</th>
          <th>Perfects</th>
        </tr>
      </thead>`;
    const tbody = document.createElement('tbody');

    games.forEach(g => {{
      const isBest  = g.total_score === bestScore;
      const allPerf = g.perfect_count === g.photo_count;
      const date    = new Date(g.played_at);
      const dateStr = date.toLocaleDateString('en-US', {{
        month: 'short', day: 'numeric', year: 'numeric'
      }});

      const bestHtml = isBest ? '<span class="best-badge">⭐ Best</span>' : '';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="td-date">${{dateStr}}</td>
        <td class="td-score ${{isBest ? 'best' : ''}}">${{g.total_score.toFixed(1)}} pts${{bestHtml}}</td>
        <td class="td-perfs ${{allPerf ? 'all-perfect' : ''}}">${{g.perfect_count ?? 0}} / ${{g.photo_count ?? 10}}</td>
      `;
      tbody.appendChild(tr);
    }});

    table.appendChild(tbody);
    wrap.appendChild(table);
    container.appendChild(wrap);

  }} else {{
    document.getElementById('hero-score').textContent     = '—';
    document.getElementById('hero-score-max').textContent = '';
    document.getElementById('hero-callout').textContent   = `No scores yet — time to hit the trail!`;
    document.getElementById('stat-avg').textContent      = '—';
    document.getElementById('stat-perfects').textContent = '—';
    document.getElementById('games-container').innerHTML =
      '<div class="no-games">No scored games yet.</div>';
  }}
}}

function getAvatarEmoji(name) {{
  // Deterministic emoji based on trail name — 10 trail-themed options
  const emojis = ['🏕','🌲','⛰','🏔','🌄','🎒','🥾','🦅','🌿','🏞'];
  if (!name) return emojis[0];
  const code = [...name].reduce((a, c) => a + c.charCodeAt(0), 0);
  return emojis[code % emojis.length];
}}

function getAvatarColor(uuid) {{
  // Deterministic background color seeded by the user's UUID.
  // Golden-angle hue spread (×137) gives even distribution across the colour wheel.
  // HSL 62% saturation, 38% lightness → vibrant but not garish; readable on dark bg.
  const code = [...(uuid || '')].reduce((a, c) => a + c.charCodeAt(0), 0);
  const hue  = (code * 137) % 360;
  return `hsl(${{hue}}, 62%, 38%)`;
}}

load();
</script>
</body>
</html>"""

with open(OUT_PATH, "w") as f:
    f.write(html)

print(f"Built {OUT_PATH}")
