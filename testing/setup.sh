#!/bin/sh
set -eu

TESTING_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VENV="$TESTING_DIR/.venv"
BROWSERS="$TESTING_DIR/.playwright-browsers"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Creating isolated Python environment..."
  python3 -m venv "$VENV"
fi

echo "Installing test dependencies..."
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$TESTING_DIR/requirements-dev.txt"

echo "Installing Chromium inside testing/..."
PLAYWRIGHT_BROWSERS_PATH="$BROWSERS" \
  "$VENV/bin/python" -m playwright install chromium

echo
echo "Setup complete."
echo "Run fast tests:  ./testing/test.sh quick"
echo "Run all tests:   ./testing/test.sh"

