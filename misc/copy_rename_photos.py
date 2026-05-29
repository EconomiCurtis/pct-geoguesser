import os
import csv
import shutil

SRC_DIR = "/Volumes/PCT2025-4T/2026 PCT GeoGuesser Game/raw-photos-save/Summer 2025"
DST_DIR = "/Volumes/PCT2025-4T/2026 PCT GeoGuesser Game/img/miles"
CSV_PATH = "/Volumes/PCT2025-4T/2026 PCT GeoGuesser Game/misc/photos.csv"

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
