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
