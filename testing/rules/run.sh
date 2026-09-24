#!/bin/sh
# Runs the Firestore security-rules tests against the local emulator.
# Needs Node and Java (brew install openjdk). Test libraries install once into
# ~/.cache so node_modules stays out of Google Drive.
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(dirname "$(dirname "$HERE")")
DEPS="$HOME/.cache/pct-geoguesser-rules-test"

if [ ! -d "$DEPS/node_modules/@firebase/rules-unit-testing" ]; then
  mkdir -p "$DEPS"
  (cd "$DEPS" && [ -f package.json ] || echo '{"name":"pct-rules-test","private":true}' > package.json
   npm install --silent @firebase/rules-unit-testing@5 firebase@12.19.0)
fi

[ -d /opt/homebrew/opt/openjdk/bin ] && PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
export PATH
export NODE_PATH="$DEPS/node_modules"
export RULES_FILE="$ROOT/firestore.rules"

cd "$HERE"
exec npx --yes firebase-tools emulators:exec --only firestore --project demo-pct-geoguesser \
  "node --test --test-reporter=spec firestore.rules.test.cjs"
