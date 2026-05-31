# ──────────────────────────────────────────────────────────────────────────────
# generate_photo_csv.py  --  PCT GeoGuesser
#
# Scans the raw photo folder and (re)builds misc/photos.csv, the master table
# with one row per photo. Each raw filename encodes the trail mile (and sometimes
# "sobo"); this script parses that out and assigns the rest of the metadata.
#
# Per photo it produces:
#   id        : random 5-letter handle, also the deployed filename (hides the answer)
#   mile      : NoBo trail mile, parsed from "Mile <n>" in the filename
#   direction : NoBo, or SoBo if "sobo" appears in the filename
#   section   : named PCT section, derived from the mile (see get_section)
#   date      : the SEASON constant below
#   filename  : original raw filename (kept so re-runs can match existing rows)
#   url       : public image URL, {IMAGE_BASE_URL}/{id}{ext}
#   version   : v1-demo or v2-scored (new rows default to v2-scored)
#   photo_by  : photographer credit (blank; set by hand in the CSV)
#   tags      : e.g. "green-tunnel" (blank; set by hand in the CSV)
#   lat/lon/map : geographic columns, left BLANK here and filled separately
#                 by add_geo_columns.py (which needs the GPS spreadsheet).
#
# Safe to re-run: existing rows are preserved exactly (IDs, manual edits, geo
# values all survive). Only raw files not already in the CSV get new rows. The
# url column is always recomputed so an IMAGE_BASE_URL change propagates.
#
# Two-step flow when adding photos:
#   1. python3 misc/generate_photo_csv.py   (this script: adds rows, blank geo)
#   2. python3 misc/add_geo_columns.py      (fills lat/lon/map for the new rows)
#
# Run:
#   python3 misc/generate_photo_csv.py
# ──────────────────────────────────────────────────────────────────────────────

import os
import re
import csv
import random
import string

PHOTO_DIR      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img", "raw-photos-save", "Summer 2025")
OUTPUT_CSV     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos.csv")
SEASON         = "Summer 2025"  # written as the "date" column; matches the source folder name
IMAGE_BASE_URL = "https://pct-geoguesser.pages.dev/miles"  # update here if hosting changes
# lat/lon/map are populated by add_geo_columns.py, not here. They are included in
# FIELDNAMES so existing geo values are preserved on re-run (and so DictWriter does
# not choke on the extra keys); new rows below leave them blank.
FIELDNAMES     = ["id", "mile", "direction", "section", "date", "filename", "url", "version", "photo_by", "tags", "lat", "lon", "map"]

def make_url(row_id, filename):
    ext = os.path.splitext(filename)[1].lower()  # .jpeg or .jpg
    return f"{IMAGE_BASE_URL}/{row_id}{ext}"

def random_id(length=5):
    # 5 random lowercase letters — short enough to be a clean filename, enough entropy
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def get_section(mile):
    # Maps a trail mile (as string or float) to its named PCT section
    m = float(mile) if mile is not None else 0.0
    if m <= 702.1:    return "Southern California"
    elif m <= 1092.3: return "The Sierra"
    elif m <= 1692.0: return "Northern California"
    elif m < 2147.0:  return "Oregon"
    else:             return "Washington"

def extract_mile(filename):
    # Handles single or double spaces after "Mile", e.g. "Mile 53.1" or "Mile  557"
    match = re.search(r'Mile\s+([\d]+\.?[\d]*)', filename, re.IGNORECASE)
    if match:
        return f"{float(match.group(1)):.1f}"  # normalize to one decimal place
    return None

# ── Load existing CSV so we can preserve all current IDs ───────
# Re-running this script is always safe: existing rows are kept exactly as-is,
# and only files not already in the CSV get new IDs assigned.
existing_rows   = []
known_filenames = set()
used_ids        = set()

if os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, newline="") as f:
        existing_rows = list(csv.DictReader(f))
    # Always recalculate url so IMAGE_BASE_URL changes propagate on next run
    for r in existing_rows:
        r["url"] = make_url(r["id"], r["filename"])
    known_filenames = {r["filename"] for r in existing_rows}
    used_ids        = {r["id"]       for r in existing_rows}

def unique_id():
    # Retry until we get a collision-free ID (birthday problem negligible at this scale)
    while True:
        uid = random_id()
        if uid not in used_ids:
            used_ids.add(uid)
            return uid

# ── Find files not yet in the CSV ──────────────────────────────
all_files = sorted(os.listdir(PHOTO_DIR))
new_rows  = []
errors    = []

for fname in all_files:
    # macOS creates invisible "._filename" resource fork files on external drives — skip them
    if fname.startswith('._') or not fname.lower().endswith(('.jpeg', '.jpg', '.png')):
        continue
    if fname in known_filenames:
        continue  # already has an ID — leave it alone

    mile = extract_mile(fname)
    if mile is None:
        errors.append(fname)
        continue

    # "sobo" anywhere in the filename (case-insensitive) marks a southbound photo
    direction = "SoBo" if re.search(r'sobo', fname, re.IGNORECASE) else "NoBo"

    uid = unique_id()
    new_rows.append({
        "id":        uid,
        "mile":      mile,
        "direction": direction,
        "section":   get_section(mile),
        "date":      SEASON,
        "filename":  fname,
        "url":       make_url(uid, fname),
        "version":   "",   # default assigned below; manual edits in CSV are always preserved
        "photo_by":  "",   # set manually after adding to CSV if needed
        "tags":      "",   # e.g. "green-tunnel" -- set manually in CSV
        "lat":       "",   # filled by add_geo_columns.py
        "lon":       "",   # filled by add_geo_columns.py
        "map":       "",   # filled by add_geo_columns.py
    })

# ── Combine and sort by mile ───────────────────────────────────────
# Versions are NEVER overwritten — manual edits in photos.csv are permanent.
# New photos with no version yet default to v2-scored (move to v1-demo by hand if desired).
all_rows = sorted(existing_rows + new_rows, key=lambda r: float(r["mile"]))
for r in all_rows:
    if not r.get("version"):
        r["version"] = "v2-scored"

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(all_rows)

print(f"photos.csv: {len(existing_rows)} existing + {len(new_rows)} new = {len(all_rows)} total")
if new_rows:
    print(f"\nNew photos added:")
    for r in new_rows:
        print(f"  {r['id']}  mile={r['mile']}  {r['direction']}  {r['section']}")
        print(f"    {r['filename']}")
if errors:
    print(f"\nCould not extract mile from {len(errors)} file(s) — skipped:")
    for e in errors:
        print(f"  {e}")
