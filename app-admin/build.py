# ──────────────────────────────────────────────────────────────────────────────
# build.py  —  PCT GeoGuesser  (admin dashboard)
#
# Generates deploy/admin/index.html — a private dashboard accessible only to
# the admin Google account (curtisesjunk@gmail.com). All reads use the public
# anon key; the email check is client-side (fine because all read data is
# already public via RLS; this just controls UI access).
#
# Four tab views:
#   - Recent Games   : last 100 scored games with player names + scores
#   - Photo Stats    : every photo merged with Supabase stats, sortable; each
#                      thumbnail opens a lightbox with a "map" deep link
#   - Edit Database  : search players, delete games or full player records
#   - Site Settings  : admin toggles (e.g. show/hide the 90-day leaderboard tab)
#
# Delete actions require two SECURITY DEFINER RPCs in Supabase:
#   admin_delete_player_games(target_user_id UUID)
#   admin_delete_player(target_user_id UUID)
# See misc/supabase_admin_rpcs.sql for the SQL to paste in Supabase.
#
# To rebuild:
#   python3 app-admin/build.py
#
# To deploy:
#   cp app-admin/index.html deploy/admin/index.html
#   npx wrangler pages deploy deploy/ --project-name=pct-geoguesser
# ──────────────────────────────────────────────────────────────────────────────

import csv
import json
import os
import sys

HERE     = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "misc"))
from supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY

CSV_PATH = os.path.join(HERE, "..", "misc", "photos.csv")
OUT_PATH = os.path.join(HERE, "index.html")

with open(CSV_PATH) as f:
    rows = list(csv.DictReader(f))

all_photos_json = json.dumps(
    [
        {
            "id":        r["id"],
            "mile":      float(r["mile"]),
            "direction": r["direction"],
            "section":   r["section"],
            "date":      r.get("date", "") or "",
            "photo_by":  r.get("photo_by", "") or "",
            "map":       r.get("map", "") or "",
            "version":   r["version"],
            "url":       r["url"],
        }
        for r in rows
    ],
    separators=(",", ":"),
)

ADMIN_EMAIL = "curtisesjunk@gmail.com"

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PCT GeoGuesser — Admin</title>
<meta name="robots" content="noindex,nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg:       #0d1117;
  --surface:  #161b22;
  --surface2: #21262d;
  --border:   #30363d;
  --text:     #f0f6fc;
  --muted:    #8b949e;
  --teal:     #008080;
  --green:    #1D502E;
  --green2:   #2ab062;
  --red:      #dc2626;
  --amber:    #f59e0b;
}}

body {{
  font-family: 'Open Sans', Arial, sans-serif;
  background: var(--bg); color: var(--text);
  font-size: 14px; line-height: 1.5;
}}

/* ── Nav ──────────────────────────────────────────────── */
nav {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px; background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 10;
}}
.nav-title {{ font-size: 15px; font-weight: 700; color: var(--teal); }}
.nav-sub   {{ font-size: 12px; color: var(--muted); margin-left: 8px; }}
nav a, nav button {{
  background: none; border: 1px solid var(--border);
  color: var(--muted); padding: 5px 14px; border-radius: 6px;
  cursor: pointer; font-size: 12px; text-decoration: none;
  transition: border-color .15s, color .15s;
}}
nav a:hover, nav button:hover {{ border-color: var(--muted); color: var(--text); }}

/* ── Layout ───────────────────────────────────────────── */
#loading-view {{ padding: 60px 20px; text-align: center; color: var(--muted); }}
#main-view    {{ display: none; padding: 24px 20px 60px; max-width: 1400px; margin: 0 auto; }}

section {{ margin-bottom: 48px; }}

/* ── Stat chips ─────────────────────────────────────── */
.overview-chips {{
  display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px;
}}
.chip {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 12px 18px; min-width: 120px;
}}
.chip-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }}
.chip-val   {{ font-size: 26px; font-weight: 700; color: var(--teal); font-variant-numeric: tabular-nums; line-height: 1.2; }}

/* ── Tab bar ──────────────────────────────────────────── */
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
  font-size: 13px; font-weight: 700;
  cursor: pointer;
  background: var(--surface); color: var(--muted);
  border: none; border-right: 1px solid var(--border);
  transition: background .15s, color .15s;
  font-family: inherit;
}}
.tab:last-child {{ border-right: none; }}
.tab:hover:not(.tab-active) {{ background: var(--surface2); color: var(--text); }}
.tab.tab-active {{ background: var(--green); color: #fff; cursor: default; }}

/* ── Tables ───────────────────────────────────────────── */
.table-wrap {{ overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{
  padding: 8px 12px; text-align: left;
  font-size: 10px; text-transform: uppercase; letter-spacing: .08em;
  color: var(--muted); border-bottom: 1px solid var(--border);
  white-space: nowrap; background: var(--surface);
}}
th.sortable {{ cursor: pointer; user-select: none; }}
th.sortable:hover {{ color: var(--teal); }}
th.sort-active {{ color: var(--teal); }}
th.sort-active::after {{ content: ' ' attr(data-arrow); }}
td {{
  padding: 7px 12px; border-bottom: 1px solid var(--border);
  vertical-align: middle; white-space: nowrap;
}}
tr:last-child td {{ border-bottom: none; }}
tr:hover td {{ background: var(--surface); }}

.td-thumb img {{
  width: 56px; height: 40px; object-fit: cover;
  border-radius: 4px; border: 1px solid var(--border); display: block;
}}
.td-thumb img:hover {{ opacity: .8; cursor: pointer; border-color: var(--teal); }}

td.val-good  {{ color: var(--teal);  font-weight: 600; }}
td.val-mid   {{ color: var(--green2); font-weight: 600; }}
td.val-bad   {{ color: var(--amber); font-weight: 600; }}
td.val-muted {{ color: var(--muted); }}

.badge {{ display: inline-block; border-radius: 4px; padding: 2px 7px; font-size: 10px; font-weight: 700; letter-spacing: .04em; }}
.badge-v1 {{ background: rgba(200,169,110,.2); color: #d4b07a; }}
.badge-v2 {{ background: rgba(0,128,128,.2);   color: var(--teal); }}

/* ── Toolbars / filters ───────────────────────────────── */
.toolbar {{ display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }}
.toolbar label {{ font-size: 12px; color: var(--muted); }}
.sort-btn {{
  background: var(--surface2); border: 1px solid var(--border);
  color: var(--muted); padding: 5px 14px; border-radius: 6px;
  cursor: pointer; font-size: 12px; transition: all .15s; font-family: inherit;
}}
.sort-btn:hover  {{ border-color: var(--muted); color: var(--text); }}
.sort-btn.active {{ background: var(--green); border-color: var(--green); color: #fff; }}

.filter-row {{ display: flex; gap: 8px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
.filter-row input {{
  background: var(--surface2); border: 1px solid var(--border);
  color: var(--text); border-radius: 6px; padding: 5px 12px;
  font-size: 13px; outline: none; width: 200px;
}}
.filter-row input:focus {{ border-color: var(--teal); }}

/* ── Edit Database ────────────────────────────────────── */
.search-bar {{ display: flex; gap: 8px; margin-bottom: 8px; align-items: center; }}
.search-bar input {{
  background: var(--surface2); border: 1px solid var(--border);
  color: var(--text); border-radius: 6px; padding: 7px 12px;
  font-size: 13px; outline: none; flex: 1; max-width: 320px; font-family: inherit;
}}
.search-bar input:focus {{ border-color: var(--teal); }}
.search-hint {{ font-size: 11px; color: var(--muted); margin-bottom: 14px; }}
#search-results .state-row {{ padding: 20px; color: var(--muted); font-size: 13px; text-align: center; }}
.results-wrap {{ border: 1px solid var(--border); border-radius: 10px; overflow: hidden; min-height: 60px; }}
.player-result-row {{
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-bottom: 1px solid var(--border); flex-wrap: wrap;
}}
.player-result-row:last-child {{ border-bottom: none; }}
.player-name    {{ font-weight: 700; color: var(--teal); min-width: 140px; flex: 1; }}
.player-year    {{ font-size: 12px; color: var(--muted); min-width: 70px; }}
.player-id      {{ font-size: 11px; color: var(--muted); font-family: monospace; min-width: 200px; }}
.player-actions {{ display: flex; gap: 6px; flex-shrink: 0; }}
.btn-warn {{
  border: 1px solid var(--amber); background: transparent; color: var(--amber);
  padding: 4px 10px; border-radius: 5px; font-size: 11px; font-weight: 700;
  cursor: pointer; transition: background .15s, color .15s; font-family: inherit;
}}
.btn-warn:hover {{ background: var(--amber); color: #000; }}
.btn-danger {{
  border: 1px solid var(--red); background: transparent; color: var(--red);
  padding: 4px 10px; border-radius: 5px; font-size: 11px; font-weight: 700;
  cursor: pointer; transition: background .15s, color .15s; font-family: inherit;
}}
.btn-danger:hover {{ background: var(--red); color: #fff; }}
.edit-note {{
  margin-top: 16px; padding: 10px 14px;
  background: rgba(245,158,11,.08); border: 1px solid rgba(245,158,11,.3);
  border-radius: 8px; font-size: 12px; color: var(--muted); line-height: 1.6;
}}
.edit-note strong {{ color: var(--amber); }}

/* ── Confirm Modal ────────────────────────────────────── */
.modal-overlay {{
  position: fixed; inset: 0; background: rgba(0,0,0,.82);
  z-index: 200; align-items: center; justify-content: center; padding: 20px;
}}
.modal-card {{
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 16px; padding: 30px 28px 24px; max-width: 410px; width: 100%;
  box-shadow: 0 24px 72px rgba(0,0,0,.75);
}}
.modal-icon  {{ font-size: 36px; margin-bottom: 10px; line-height: 1; }}
.modal-title {{ font-size: 19px; font-weight: 800; margin-bottom: 12px; }}
.modal-body  {{
  font-size: 13px; color: var(--muted); line-height: 1.7;
  margin-bottom: 24px;
}}
.modal-body strong {{ color: var(--text); }}
.modal-body .danger-text {{ color: var(--red); font-weight: 700; }}
.modal-body .warn-text   {{ color: var(--amber); font-weight: 700; }}
.modal-actions {{ display: flex; gap: 10px; justify-content: flex-end; }}
.btn-modal-cancel {{
  background: var(--surface); border: 1px solid var(--border);
  color: var(--muted); padding: 9px 22px; border-radius: 8px;
  cursor: pointer; font-size: 13px; font-weight: 600; font-family: inherit;
  transition: all .15s;
}}
.btn-modal-cancel:hover {{ border-color: var(--muted); color: var(--text); }}
.btn-modal-confirm {{
  border: none; padding: 9px 22px; border-radius: 8px;
  cursor: pointer; font-size: 13px; font-weight: 700; font-family: inherit;
  transition: filter .15s;
}}
.btn-modal-confirm:hover {{ filter: brightness(1.18); }}

/* ── Toggle switch ────────────────────────────────────── */
.toggle-switch {{
  position: relative; display: inline-block;
  width: 48px; height: 26px; flex-shrink: 0;
}}
.toggle-switch input {{ opacity: 0; width: 0; height: 0; }}
.toggle-slider {{
  position: absolute; inset: 0; background: var(--surface2);
  border: 1px solid var(--border); border-radius: 26px;
  cursor: pointer; transition: background .2s, border-color .2s;
}}
.toggle-slider::before {{
  content: ''; position: absolute;
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--muted); left: 3px; top: 3px;
  transition: transform .2s, background .2s;
}}
.toggle-switch input:checked + .toggle-slider {{
  background: var(--teal); border-color: var(--teal);
}}
.toggle-switch input:checked + .toggle-slider::before {{
  transform: translateX(22px); background: #fff;
}}
</style>
</head>
<body>

<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>

<div id="loading-view">Checking authentication…</div>

<nav id="nav-bar" style="display:none">
  <div>
    <span class="nav-title">PCT GeoGuesser Admin</span>
    <span class="nav-sub" id="nav-user"></span>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <a href="/">← Site</a>
    <button onclick="refreshAll()" title="Reload stats from Supabase">⟳ Refresh</button>
    <button onclick="doSignOut()">Sign out</button>
  </div>
</nav>

<div id="main-view">

  <!-- ── Overview chips ─────────────────────────────── -->
  <div class="overview-chips">
    <div class="chip"><div class="chip-label">Total Games</div><div class="chip-val" id="chip-games">—</div></div>
    <div class="chip"><div class="chip-label">Unique Players</div><div class="chip-val" id="chip-players">—</div></div>
    <div class="chip"><div class="chip-label">Photos w/ Data</div><div class="chip-val" id="chip-photos">—</div></div>
  </div>

  <!-- ── Tab bar ────────────────────────────────────── -->
  <div class="tab-bar">
    <button class="tab tab-active" onclick="switchTab('games')">Recent Games (last 100)</button>
    <button class="tab"            onclick="switchTab('stats')">Photo Stats</button>
    <button class="tab"            onclick="switchTab('edit')">Edit Database</button>
    <button class="tab"            onclick="switchTab('settings')">Site Settings</button>
  </div>

  <!-- ── VIEW: Recent Games ─────────────────────────── -->
  <section id="view-games">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Trail Name</th><th>PCT Year</th><th>Score</th><th>Perfects</th><th>Played</th>
          </tr>
        </thead>
        <tbody id="games-tbody"></tbody>
      </table>
    </div>
  </section>

  <!-- ── VIEW: Photo Stats ──────────────────────────── -->
  <section id="view-stats" style="display:none">
    <div class="toolbar">
      <label>Sort by:</label>
      <button class="sort-btn active" id="sort-mile" onclick="setSort('mile')">Mile ↑</button>
      <button class="sort-btn" id="sort-mean"  onclick="setSort('avg_error')">Mean Error</button>
      <button class="sort-btn" id="sort-sd"    onclick="setSort('v_sd')">SD</button>
      <button class="sort-btn" id="sort-n"     onclick="setSort('n_guesses')">N Guesses</button>
    </div>
    <div class="filter-row">
      <input type="text" id="section-filter" placeholder="Filter by section…" oninput="renderStats()">
      <button class="sort-btn" id="filter-v1" onclick="toggleVersionFilter('v1-demo')">v1</button>
      <button class="sort-btn" id="filter-v2" onclick="toggleVersionFilter('v2-scored')">v2</button>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th style="width:72px">Photo</th>
            <th class="sortable sort-active" id="th-mile"          data-arrow="↑" onclick="setSort('mile')">Mile</th>
            <th>Section</th><th>Dir</th><th>Date</th><th>Photo By</th><th>Pool</th>
            <th class="sortable" id="th-appearances"  onclick="setSort('appearances')">Shown</th>
            <th class="sortable" id="th-n_guesses"    onclick="setSort('n_guesses')">N</th>
            <th class="sortable" id="th-avg_error"    onclick="setSort('avg_error')">Mean Error</th>
            <th class="sortable" id="th-v_sd"         onclick="setSort('v_sd')">SD</th>
            <th class="sortable" id="th-perfect_count" onclick="setSort('perfect_count')">Perfects</th>
            <th>Perfect %</th>
          </tr>
        </thead>
        <tbody id="stats-tbody"></tbody>
      </table>
    </div>
  </section>

  <!-- ── VIEW: Site Settings ──────────────────────── -->
  <section id="view-settings" style="display:none">
    <div style="max-width:480px;display:flex;flex-direction:column;gap:24px;padding:8px 0">
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px 24px;display:flex;flex-direction:column;gap:12px">
        <div style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--teal)">Leaderboard</div>
        <div style="display:flex;justify-content:space-between;align-items:center;gap:16px">
          <div>
            <div style="font-size:15px;font-weight:600">Show 90-Day Leaderboard</div>
            <div style="font-size:12px;color:var(--muted);margin-top:3px">When on, a "90-Day" tab appears on /leaderboard/ alongside All-Time.</div>
          </div>
          <label class="toggle-switch">
            <input type="checkbox" id="toggle-rolling" onchange="saveSetting('show_rolling_leaderboard', this.checked)">
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>
      <p id="settings-status" style="font-size:13px;color:var(--muted);text-align:center;min-height:18px"></p>
    </div>
  </section>

  <!-- ── VIEW: Edit Database ────────────────────────── -->
  <section id="view-edit" style="display:none">
    <div class="search-bar">
      <input type="text" id="search-input" placeholder="Search by trail name…" oninput="debounceSearch()">
      <button class="sort-btn" onclick="doSearch()">Search</button>
    </div>
    <p class="search-hint">Empty = 25 most recent signups &nbsp;·&nbsp; Partial match, case-insensitive</p>
    <div class="results-wrap">
      <div id="search-results">
        <div class="state-row">Type a name above, or leave blank and hit Search to see recent signups.</div>
      </div>
    </div>
    <div class="edit-note">
      <strong>⚠ "Delete Player"</strong> removes the profile and all game data.
      Their Google auth account remains — remove it from <strong>Supabase → Authentication → Users</strong> to prevent re-signup.<br>
      <strong>⚠ Photo stats</strong> are not recalculated after a delete.
    </div>
  </section>

</div>

<!-- ── Confirm Modal ──────────────────────────────────────── -->
<div id="confirm-modal" class="modal-overlay" style="display:none">
  <div class="modal-card">
    <div class="modal-icon"  id="modal-icon">⚠️</div>
    <h2 class="modal-title"  id="modal-title">Are you sure?</h2>
    <div class="modal-body"  id="modal-body"></div>
    <div class="modal-actions">
      <button class="btn-modal-cancel"  onclick="closeConfirm()">Cancel</button>
      <button class="btn-modal-confirm" id="modal-confirm-btn"   onclick="execConfirm()">Delete</button>
    </div>
  </div>
</div>

<!-- ── Lightbox ───────────────────────────────────────────── -->
<div id="lb" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.9);z-index:100;align-items:center;justify-content:center;flex-direction:column;gap:10px" onclick="this.style.display='none'">
  <img id="lb-img" style="max-width:90vw;max-height:85vh;object-fit:contain;border-radius:6px">
  <p  id="lb-cap" style="color:var(--muted);font-size:13px"></p>
</div>

<script>
const ADMIN_EMAIL = '{ADMIN_EMAIL}';
const allPhotos   = {all_photos_json};

const {{ createClient }} = supabase;
const sb = createClient('{SUPABASE_URL}', '{SUPABASE_ANON_KEY}');

// ── Auth ──────────────────────────────────────────────────
sb.auth.onAuthStateChange(async (event, session) => {{
  if (event === 'INITIAL_SESSION') {{
    if (!session || session.user.email !== ADMIN_EMAIL) {{
      document.getElementById('loading-view').textContent =
        session ? 'Access denied.' : 'Not signed in — go to /game/ first.';
      return;
    }}
    document.getElementById('nav-user').textContent = session.user.email;
    document.getElementById('nav-bar').style.display = 'flex';
    await Promise.all([loadAdminData(), loadSettings()]);
  }} else if (event === 'SIGNED_OUT') {{
    window.location.href = '/';
  }}
}});

async function doSignOut() {{ await sb.auth.signOut(); }}

// ── Tab switching ─────────────────────────────────────────
const TABS = ['games', 'stats', 'edit', 'settings'];
function switchTab(tab) {{
  TABS.forEach(t => {{
    document.getElementById('view-' + t).style.display = (t === tab) ? '' : 'none';
  }});
  document.querySelectorAll('.tab-bar .tab').forEach((btn, i) => {{
    btn.classList.toggle('tab-active', TABS[i] === tab);
  }});
}}

// ── Site Settings ─────────────────────────────────────────
async function loadSettings() {{
  try {{
    const {{ data }} = await sb
      .from('site_settings')
      .select('key, value');
    if (!data) return;
    for (const row of data) {{
      if (row.key === 'show_rolling_leaderboard') {{
        document.getElementById('toggle-rolling').checked = row.value === 'true';
      }}
    }}
  }} catch (_) {{}}
}}

async function saveSetting(key, value) {{
  const statusEl = document.getElementById('settings-status');
  statusEl.textContent = 'Saving…';
  statusEl.style.color = 'var(--muted)';
  const {{ error }} = await sb.rpc('admin_set_setting', {{
    p_key:   key,
    p_value: String(value),
  }});
  if (error) {{
    statusEl.textContent = 'Error: ' + error.message;
    statusEl.style.color = 'var(--red)';
  }} else {{
    statusEl.textContent = 'Saved ✓';
    statusEl.style.color = 'var(--teal)';
    setTimeout(() => {{ statusEl.textContent = ''; }}, 2500);
  }}
}}

// ── Data loading ──────────────────────────────────────────
let mergedPhotos = [], sortKey = 'mile', sortAsc = true, versionFilter = null;

async function loadAdminData() {{
  const [gamesRes, statsRes, playerCountRes, gameCountRes] = await Promise.all([
    sb.from('game_sessions')
      .select('total_score, perfect_count, photo_count, played_at, profiles(id, trail_name, pct_year)')
      .order('played_at', {{ ascending: false }}).limit(100),
    sb.from('photo_stats').select('photo_id, appearances, n_guesses, avg_error, v_sd, perfect_count'),
    sb.from('profiles').select('id', {{ count: 'exact', head: true }}),
    sb.from('game_sessions').select('id', {{ count: 'exact', head: true }}),
  ]);

  document.getElementById('chip-games').textContent   = (gameCountRes.count   ?? '—').toLocaleString();
  document.getElementById('chip-players').textContent = (playerCountRes.count ?? '—').toLocaleString();
  renderGames(gamesRes.data || []);

  const statsMap = {{}};
  for (const s of (statsRes.data || [])) statsMap[s.photo_id] = s;
  document.getElementById('chip-photos').textContent = Object.keys(statsMap).length;

  mergedPhotos = allPhotos.map(p => ({{
    ...p,
    appearances:   statsMap[p.id]?.appearances  ?? 0,
    n_guesses:     statsMap[p.id]?.n_guesses    ?? 0,
    avg_error:     statsMap[p.id]?.avg_error     ?? null,
    v_sd:          statsMap[p.id]?.v_sd          ?? null,
    perfect_count: statsMap[p.id]?.perfect_count ?? 0,
  }}));
  renderStats();

  document.getElementById('loading-view').style.display = 'none';
  document.getElementById('main-view').style.display    = 'block';
}}

async function refreshChips() {{
  const [pRes, gRes] = await Promise.all([
    sb.from('profiles').select('id', {{ count: 'exact', head: true }}),
    sb.from('game_sessions').select('id', {{ count: 'exact', head: true }}),
  ]);
  document.getElementById('chip-games').textContent   = (gRes.count ?? '—').toLocaleString();
  document.getElementById('chip-players').textContent = (pRes.count ?? '—').toLocaleString();
}}

async function refreshAll() {{
  const btn = document.querySelector('button[onclick="refreshAll()"]');
  if (btn) {{ btn.disabled = true; btn.textContent = '⟳ Refreshing…'; }}
  await loadAdminData();
  // Also clear search results so they don't show stale data
  document.getElementById('search-results').innerHTML =
    '<div class="state-row">Data refreshed. Run a search to see updated players.</div>';
  if (btn) {{ btn.disabled = false; btn.textContent = '⟳ Refresh'; }}
}}

// ── Recent games table ────────────────────────────────────
function renderGames(games) {{
  const tbody = document.getElementById('games-tbody');
  tbody.innerHTML = '';
  if (!games.length) {{
    tbody.innerHTML = '<tr><td colspan="5" style="color:var(--muted);text-align:center;padding:20px">No games yet.</td></tr>';
    return;
  }}
  for (const g of games) {{
    const p = g.profiles;
    const date = new Date(g.played_at);
    const dateStr = date.toLocaleDateString('en-US', {{ month:'short', day:'numeric', year:'numeric' }})
                  + ' ' + date.toLocaleTimeString('en-US', {{ hour:'2-digit', minute:'2-digit' }});
    const hikerUrl  = p?.id ? `/hiker/?id=${{p.id}}` : null;
    const nameHtml  = p?.trail_name
      ? (hikerUrl ? `<a href="${{hikerUrl}}" style="color:var(--teal);font-weight:600;text-decoration:none" target="_blank">${{p.trail_name}}</a>`
                  : `<span style="color:var(--teal);font-weight:600">${{p.trail_name}}</span>`)
      : '—';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${{nameHtml}}</td>
      <td style="color:var(--muted)">${{p?.pct_year ?? '—'}}</td>
      <td style="font-variant-numeric:tabular-nums;font-weight:600">${{Number(g.total_score).toFixed(1)}}</td>
      <td style="color:var(--muted)">${{g.perfect_count}} / ${{g.photo_count}}</td>
      <td style="color:var(--muted);font-size:12px">${{dateStr}}</td>`;
    tbody.appendChild(tr);
  }}
}}

// ── Photo stats table ─────────────────────────────────────
function setSort(key) {{
  if (sortKey === key) {{ sortAsc = !sortAsc; }} else {{ sortKey = key; sortAsc = (key === 'mile'); }}
  document.querySelectorAll('.sort-btn[id^="sort-"]').forEach(b => b.classList.remove('active'));
  const btnMap = {{ mile:'sort-mile', avg_error:'sort-mean', v_sd:'sort-sd', n_guesses:'sort-n' }};
  if (btnMap[key]) document.getElementById(btnMap[key]).classList.add('active');
  document.querySelectorAll('th.sortable').forEach(th => {{ th.classList.remove('sort-active'); delete th.dataset.arrow; }});
  const thEl = document.getElementById('th-' + key);
  if (thEl) {{ thEl.classList.add('sort-active'); thEl.dataset.arrow = sortAsc ? '↑' : '↓'; }}
  renderStats();
}}

function toggleVersionFilter(v) {{
  versionFilter = (versionFilter === v) ? null : v;
  document.getElementById('filter-v1').classList.toggle('active', versionFilter === 'v1-demo');
  document.getElementById('filter-v2').classList.toggle('active', versionFilter === 'v2-scored');
  renderStats();
}}

function renderStats() {{
  const sectionQ = document.getElementById('section-filter').value.trim().toLowerCase();
  let photos = mergedPhotos.filter(p => {{
    if (versionFilter && p.version !== versionFilter) return false;
    if (sectionQ && !p.section.toLowerCase().includes(sectionQ)) return false;
    return true;
  }});
  photos.sort((a, b) => {{
    let va = a[sortKey], vb = b[sortKey];
    const aN = va == null, bN = vb == null;
    if (aN && bN) return 0; if (aN) return 1; if (bN) return -1;
    return sortAsc ? va - vb : vb - va;
  }});
  const tbody = document.getElementById('stats-tbody');
  tbody.innerHTML = '';
  for (const p of photos) {{
    const mean = p.avg_error !== null ? p.avg_error.toFixed(1) : '—';
    const sd   = p.v_sd      !== null ? p.v_sd.toFixed(1)      : '—';
    const perfPct = p.n_guesses > 0 ? Math.round(p.perfect_count / p.n_guesses * 100) + '%' : '—';
    let meanClass = 'val-muted';
    if (p.avg_error !== null) {{
      if (p.avg_error < 50) meanClass = 'val-good';
      else if (p.avg_error < 150) meanClass = 'val-mid';
      else meanClass = 'val-bad';
    }}
    const tr = document.createElement('tr');
    const lbMeta    = `Mile ${{p.mile}} · ${{p.section}} · ${{p.direction}}${{p.date ? ' · ' + p.date : ''}}`;
    const lbCaption = p.photo_by ? lbMeta + '|📷 ' + p.photo_by : lbMeta;
    tr.innerHTML = `
      <td class="td-thumb"><img src="${{p.url}}" alt="Mile ${{p.mile}}"
           onclick="openLb('${{p.url}}', '${{lbCaption.replace(/'/g,'&#39;')}}', '${{(p.map||'').replace(/'/g,'&#39;')}}')" loading="lazy"></td>
      <td style="font-weight:700;font-variant-numeric:tabular-nums">${{p.mile}}</td>
      <td style="color:var(--muted);font-size:12px">${{p.section}}</td>
      <td style="color:var(--muted)">${{p.direction}}</td>
      <td style="color:var(--muted);font-size:12px">${{p.date || '—'}}</td>
      <td style="color:var(--muted);font-size:12px;font-style:italic">${{p.photo_by || ''}}</td>
      <td><span class="badge ${{p.version==='v1-demo'?'badge-v1':'badge-v2'}}">${{p.version==='v1-demo'?'v1':'v2'}}</span></td>
      <td class="val-muted">${{p.appearances}}</td>
      <td class="val-muted">${{p.n_guesses}}</td>
      <td class="${{meanClass}}">${{mean}}</td>
      <td class="val-muted">${{sd}}</td>
      <td class="val-muted">${{p.perfect_count}}</td>
      <td class="val-muted">${{perfPct}}</td>`;
    tbody.appendChild(tr);
  }}
}}

// ── Confirm modal ─────────────────────────────────────────
let pendingConfirmFn = null;

function showConfirm(opts) {{
  document.getElementById('modal-icon').textContent      = opts.icon       || '⚠️';
  document.getElementById('modal-title').textContent     = opts.title      || 'Are you sure?';
  document.getElementById('modal-title').style.color     = opts.titleColor || 'var(--text)';
  document.getElementById('modal-body').innerHTML        = opts.body       || '';
  const btn = document.getElementById('modal-confirm-btn');
  btn.textContent       = opts.btnLabel    || 'Confirm';
  btn.style.background  = opts.btnColor    || 'var(--red)';
  btn.style.color       = opts.btnTextColor || '#fff';
  pendingConfirmFn = opts.action || null;
  document.getElementById('confirm-modal').style.display = 'flex';
}}

function closeConfirm() {{
  document.getElementById('confirm-modal').style.display = 'none';
  pendingConfirmFn = null;
}}

function execConfirm() {{
  closeConfirm();
  if (pendingConfirmFn) pendingConfirmFn();
}}

// Close modal on overlay click
document.getElementById('confirm-modal').addEventListener('click', function(e) {{
  if (e.target === this) closeConfirm();
}});

// ── Edit Database ─────────────────────────────────────────
let searchTimer = null;
function debounceSearch() {{
  clearTimeout(searchTimer);
  searchTimer = setTimeout(doSearch, 350);
}}

async function doSearch() {{
  const q = document.getElementById('search-input').value.trim();
  const resultsEl = document.getElementById('search-results');
  resultsEl.innerHTML = '<div class="state-row">Searching…</div>';

  let query;
  if (q) {{
    query = sb.from('profiles').select('id, trail_name, pct_year')
      .ilike('trail_name', `%${{q}}%`).order('trail_name').limit(25);
  }} else {{
    query = sb.from('profiles').select('id, trail_name, pct_year')
      .order('id', {{ ascending: false }}).limit(25);
  }}

  const {{ data, error }} = await query;
  if (error) {{
    resultsEl.innerHTML = `<div class="state-row" style="color:var(--red)">Error: ${{error.message}}</div>`;
    return;
  }}
  if (!data?.length) {{
    resultsEl.innerHTML = '<div class="state-row">No players found.</div>';
    return;
  }}
  resultsEl.innerHTML = '';
  for (const p of data) {{
    const name = p.trail_name || '(no name)';
    const year = p.pct_year ? 'PCT ' + p.pct_year : '—';
    const row  = document.createElement('div');
    row.className = 'player-result-row';
    row.id = 'player-row-' + p.id;
    // Build static content
    row.innerHTML = `
      <a href="/hiker/?id=${{p.id}}" target="_blank" class="player-name" style="color:var(--teal);text-decoration:none">${{name}}</a>
      <span class="player-year">${{year}}</span>
      <span class="player-id">${{p.id}}</span>
      <div class="player-actions" id="actions-${{p.id}}"></div>`;
    resultsEl.appendChild(row);
    // Fill action buttons via DOM API (avoids nested string-escaping)
    restoreActions(p.id, name);
  }}
}}

async function getGameCount(userId) {{
  const {{ count }} = await sb.from('game_sessions')
    .select('id', {{ count: 'exact', head: true }}).eq('user_id', userId);
  return count ?? 0;
}}

// ── Delete Games ──────────────────────────────────────────
async function deleteGames(userId, trailName) {{
  const n = await getGameCount(userId);
  showConfirm({{
    icon: '🗑️',
    title: 'Delete Games?',
    titleColor: 'var(--amber)',
    body: `Delete <strong>${{n}} game session(s)</strong> for <strong>"${{trailName}}"</strong>.<br><br>
           Their <strong>profile and login account are kept</strong> — only their game history will be removed.<br><br>
           <span class="warn-text">⚠ Photo stats will not be recalculated automatically.</span><br><br>
           <span class="warn-text">This cannot be undone.</span>`,
    btnLabel:    'Yes, Delete Games',
    btnColor:    'var(--amber)',
    btnTextColor: '#000',
    action: () => doDeleteGames(userId, trailName),
  }});
}}

async function doDeleteGames(userId, trailName) {{
  const row = document.getElementById('player-row-' + userId);
  if (row) row.querySelectorAll('button').forEach(b => {{ b.disabled = true; b.textContent = 'Deleting…'; }});

  const {{ error }} = await sb.rpc('admin_delete_player_games', {{ target_user_id: userId }});
  if (error) {{
    alert('Error: ' + error.message);
    if (row) row.querySelectorAll('button').forEach((b, i) => {{
      b.disabled = false; b.textContent = i === 0 ? 'Delete Games' : 'Delete Player';
    }});
    return;
  }}
  if (row) {{
    row.style.opacity = '.4';
    row.querySelectorAll('button').forEach(b => {{ b.disabled = true; b.textContent = '✓ Done'; }});
  }}
  refreshChips();
}}

// ── Delete Player ─────────────────────────────────────────
async function deletePlayer(userId, trailName) {{
  const n = await getGameCount(userId);
  showConfirm({{
    icon: '⛔',
    title: 'Delete Player?',
    titleColor: 'var(--red)',
    body: `Permanently delete player <strong>"${{trailName}}"</strong> and their <strong>${{n}} game(s)</strong>.<br><br>
           Their <span class="danger-text">profile and all game data will be permanently removed</span>.<br><br>
           <span class="warn-text">⚠ Their Google auth account will remain.</span>
           Go to <strong>Supabase → Authentication → Users</strong> and delete it there too to prevent re-signup.<br><br>
           <span class="danger-text">This cannot be undone.</span>`,
    btnLabel: 'Yes, Delete Player',
    btnColor: 'var(--red)',
    action: () => doDeletePlayer(userId, trailName),
  }});
}}

async function doDeletePlayer(userId, trailName) {{
  const row = document.getElementById('player-row-' + userId);
  if (row) row.querySelectorAll('button').forEach(b => {{ b.disabled = true; b.textContent = 'Deleting…'; }});

  const {{ error }} = await sb.rpc('admin_delete_player', {{ target_user_id: userId }});
  if (error) {{
    alert('Error: ' + error.message);
    if (row) row.querySelectorAll('button').forEach((b, i) => {{
      b.disabled = false; b.textContent = i === 0 ? 'Delete Games' : 'Delete Player';
    }});
    return;
  }}
  if (row) row.remove();
  refreshChips();
}}

// ── Inline name editing ───────────────────────────────────
function restoreActions(userId, name) {{
  const actionsEl = document.getElementById('actions-' + userId);
  if (!actionsEl) return;
  const editBtn = document.createElement('button');
  editBtn.className = 'sort-btn';
  editBtn.style.cssText = 'font-size:11px;padding:3px 9px';
  editBtn.textContent = 'Edit Name';
  editBtn.onclick = () => startEditName(userId, name);
  const delGBtn = document.createElement('button');
  delGBtn.className = 'btn-warn';
  delGBtn.textContent = 'Delete Games';
  delGBtn.onclick = () => deleteGames(userId, name);
  const delPBtn = document.createElement('button');
  delPBtn.className = 'btn-danger';
  delPBtn.textContent = 'Delete Player';
  delPBtn.onclick = () => deletePlayer(userId, name);
  actionsEl.replaceChildren(editBtn, delGBtn, delPBtn);
}}

function startEditName(userId, currentName) {{
  const actionsEl = document.getElementById('actions-' + userId);
  if (!actionsEl) return;
  const input = document.createElement('input');
  input.type  = 'text';
  input.value = currentName;
  input.style.cssText = 'background:var(--surface2);border:1px solid var(--teal);color:var(--text);border-radius:5px;padding:3px 8px;font-size:12px;font-family:inherit;outline:none;width:160px';
  input.onkeydown = e => {{
    if (e.key === 'Enter')  saveEditedName(userId);
    if (e.key === 'Escape') cancelEditName(userId, currentName);
  }};
  const saveBtn = document.createElement('button');
  saveBtn.className = 'sort-btn';
  saveBtn.style.cssText = 'font-size:11px;padding:3px 9px;border-color:var(--teal);color:var(--teal)';
  saveBtn.textContent = 'Save';
  saveBtn.onclick = () => saveEditedName(userId);
  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'sort-btn';
  cancelBtn.style.cssText = 'font-size:11px;padding:3px 9px';
  cancelBtn.textContent = 'Cancel';
  cancelBtn.onclick = () => cancelEditName(userId, currentName);
  actionsEl.replaceChildren(input, saveBtn, cancelBtn);
  input.focus();
}}

async function saveEditedName(userId) {{
  const actionsEl = document.getElementById('actions-' + userId);
  const input   = actionsEl?.querySelector('input');
  const newName = input?.value.trim();
  if (!newName) {{ alert('Name cannot be empty.'); return; }}

  if (actionsEl) actionsEl.style.opacity = '.5';

  const {{ error }} = await sb.rpc('admin_update_player_name', {{
    target_user_id: userId,
    new_name:       newName,
  }});

  if (actionsEl) actionsEl.style.opacity = '1';

  if (error) {{
    alert('Error: ' + error.message);
    return;
  }}

  // Update the displayed name in the row
  const row    = document.getElementById('player-row-' + userId);
  const nameEl = row?.querySelector('.player-name');
  if (nameEl) nameEl.textContent = newName;

  restoreActions(userId, newName);
}}

function cancelEditName(userId, originalName) {{
  restoreActions(userId, originalName);
}}

// ── Lightbox ──────────────────────────────────────────────
function openLb(url, cap, mapUrl) {{
  document.getElementById('lb-img').src = url;
  const [meta, credit] = cap.split('|');
  const mapHtml = mapUrl
    ? ` <a href="${{mapUrl}}" target="_blank" rel="noopener" style="color:var(--teal);text-decoration:none;font-style:normal">map ↗</a>`
    : '';
  const creditHtml = credit
    ? '<br><span style="opacity:.7">' + credit + (mapUrl ? ' · ' + mapHtml.trim() : '') + '</span>'
    : (mapUrl ? '<br>' + mapHtml.trim() : '');
  document.getElementById('lb-cap').innerHTML = meta + creditHtml;
  document.getElementById('lb').style.display = 'flex';
}}
</script>
</body>
</html>
"""

with open(OUT_PATH, "w") as f:
    f.write(html)

print(f"Built {OUT_PATH}")
print(f"  {len(rows)} total photos baked in")
