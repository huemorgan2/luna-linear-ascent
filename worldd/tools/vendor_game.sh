#!/usr/bin/env bash
# Copy the game engine package from the plugin submodule into worldd/vendor
# so the Render build never depends on submodule cloning. Run before any
# deploy commit; vendor/ is committed to git on purpose.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HERE/../plugin-linear-ascent/plugin_linear_ascent"
DST="$HERE/vendor/plugin_linear_ascent"
[ -d "$SRC" ] || { echo "plugin package not found: $SRC" >&2; exit 1; }
rm -rf "$DST"
mkdir -p "$HERE/vendor"
cp -R "$SRC" "$DST"
find "$DST" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
echo "vendored -> $DST ($(find "$DST" -name '*.py' | wc -l | tr -d ' ') py files, $(find "$DST" -name '*.yaml' | wc -l | tr -d ' ') yaml)"
