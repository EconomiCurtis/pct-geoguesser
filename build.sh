#!/bin/bash
# build.sh — PCT GeoGuesser
#
# Generates all HTML pages and places them in deploy/.
# Run this locally before deploying.
#
# Photos (deploy/miles/, 637 MB) are gitignored — copy them via
#   python3 misc/copy_rename_photos.py
# before the first deploy on a new machine.
#
# To rebuild HTML:
#   bash build.sh
#
# To deploy to Cloudflare Pages (manual — not git-triggered):
#   npx wrangler pages deploy deploy/ --project-name=pct-geoguesser

set -e  # stop on first error

# Ensure all deploy subdirectories exist (git doesn't track empty dirs)
mkdir -p deploy/practice \
         deploy/game \
         deploy/leaderboard \
         deploy/hiker \
         deploy/admin

# Generate HTML for each page
python3 app-landing/build.py
python3 app-game/build.py
python3 app-leaderboard/build.py
python3 app-hiker/build.py
python3 app-admin/build.py

# Copy generated HTML into deploy/
cp app-landing/index.html                      deploy/index.html
cp app-game/practice/index.html                deploy/practice/index.html
cp app-game/scored/index.html                  deploy/game/index.html
cp app-leaderboard/index.html                  deploy/leaderboard/index.html
cp app-hiker/index.html                        deploy/hiker/index.html
cp app-admin/index.html                        deploy/admin/index.html

echo "Build complete. Output in: deploy/"
