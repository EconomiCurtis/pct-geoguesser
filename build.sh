#!/bin/bash
# build.sh — PCT GeoGuesser
#
# Run by Cloudflare Pages on every push to the GitHub repo.
# Generates all HTML pages and places them in deploy/.
# Photos (deploy/miles/) and logos (deploy/misc/) are tracked in git and
# need no regeneration — only the HTML files are rebuilt here.
#
# Cloudflare Pages settings:
#   Build command:    bash build.sh
#   Output directory: deploy
#
# To run locally (from the repo root):
#   bash build.sh

set -e  # stop on first error

# Ensure all deploy subdirectories exist (git doesn't track empty dirs)
mkdir -p deploy/practice \
         deploy/game \
         deploy/leaderboard/all-time \
         deploy/hiker \
         deploy/admin

# Generate HTML for each page
python3 app-landing/build.py
python3 app-game-v1-testing/build.py
python3 app-game-v2/build.py
python3 app-leaderboard/build.py
python3 app-hiker/build.py
python3 app-admin/build.py

# Copy generated HTML into deploy/
cp app-landing/index.html                      deploy/index.html
cp app-game-v1-testing/index.html              deploy/practice/index.html
cp app-game-v2/index.html                      deploy/game/index.html
cp app-leaderboard/index.html                  deploy/leaderboard/index.html
cp app-leaderboard/all-time/index.html         deploy/leaderboard/all-time/index.html
cp app-hiker/index.html                        deploy/hiker/index.html
cp app-admin/index.html                        deploy/admin/index.html

echo "Build complete. Output in: deploy/"
