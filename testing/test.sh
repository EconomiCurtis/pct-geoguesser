#!/bin/sh
set -eu

TESTING_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(dirname "$TESTING_DIR")
PYTHON="$TESTING_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "Test environment not found."
  echo "Run ./testing/setup.sh first."
  exit 1
fi

export PLAYWRIGHT_BROWSERS_PATH="$TESTING_DIR/.playwright-browsers"
export PYTHONDONTWRITEBYTECODE=1
cd "$PROJECT_DIR"

case "${1:-all}" in
  quick)
    exec "$PYTHON" -m pytest -c testing/pytest.ini testing -m "unit or data"
    ;;
  browser)
    exec "$PYTHON" -m pytest -c testing/pytest.ini testing -m browser
    ;;
  all)
    exec "$PYTHON" -m pytest -c testing/pytest.ini testing -m "not staging"
    ;;
  *)
    echo "Usage: ./testing/test.sh [quick|browser]"
    exit 2
    ;;
esac
