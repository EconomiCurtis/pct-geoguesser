# ──────────────────────────────────────────────────────────────────────────────
# copy_rename_photos.py  --  PCT GeoGuesser
#
# Copies each raw photo into deploy/miles/ under its anonymized name. The raw
# files have descriptive names that leak the answer (they contain the mile);
# the deployed copy is renamed to just {id}{ext} so the URL gives nothing away.
#
# Reads misc/photos.csv for the filename -> id mapping. For every row:
#   img/raw-photos-save/Summer 2025/<filename>  ->  deploy/miles/<id><ext>
#
# Safe to re-run: files already present in deploy/miles/ are skipped, originals
# are never modified (copy2 preserves timestamps). Rows whose source file is
# missing are reported at the end rather than aborting the run.
#
# Note: both img/ (source) and deploy/miles/ (637 MB of photos) are gitignored,
# so this only does useful work on a machine that has the raw photos locally.
#
# Run:
#   python3 misc/copy_rename_photos.py
# ──────────────────────────────────────────────────────────────────────────────

import os
import csv
import shutil

_HERE    = os.path.dirname(os.path.abspath(__file__))
SRC_DIR  = os.path.join(_HERE, "..", "img", "raw-photos-save", "Summer 2025")
DST_DIR  = os.path.join(_HERE, "..", "deploy", "miles")
CSV_PATH = os.path.join(_HERE, "photos.csv")

os.makedirs(DST_DIR, exist_ok=True)  # create destination if it doesn't already exist

copied  = 0
skipped = 0
errors  = []

with open(CSV_PATH, newline="") as f:
    for row in csv.DictReader(f):
        src = os.path.join(SRC_DIR, row["filename"])
        ext = os.path.splitext(row["filename"])[1]  # preserve original extension (.jpeg)
        dst = os.path.join(DST_DIR, row["id"] + ext)  # new filename is just the random id

        if not os.path.exists(src):
            errors.append(f"MISSING SOURCE: {row['filename']}")
            continue

        if os.path.exists(dst):
            skipped += 1  # already copied on a previous run — skip to avoid unnecessary I/O
            continue

        shutil.copy2(src, dst)  # copy2 preserves file timestamps; originals are never touched
        copied += 1

print(f"Copied {copied} new file(s), skipped {skipped} already present  →  {DST_DIR}")
if errors:
    print(f"\n{len(errors)} error(s):")
    for e in errors:
        print(f"  {e}")
