#!/usr/bin/env bash
# Copy the game engine package from the plugin submodule into worldd/vendor
# so the Render build never depends on submodule cloning. Run before any
# deploy commit; vendor/ is committed to git on purpose.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HERE/../plugin-linear-ascent/plugin_linear_ascent"
DST="$HERE/vendor/plugin_linear_ascent"
[ -d "$SRC" ] || { echo "plugin package not found: $SRC" >&2; exit 1; }
mkdir -p "$DST"
# rsync, not rm -rf + cp: the tree is ~800 files of art on a cloud-synced
# disk, where a full re-copy costs hours and leaves the whole vendor
# directory missing from git if it is interrupted. --delete keeps it an
# exact mirror either way.
rsync -a --delete --exclude '__pycache__' "$SRC/" "$DST/"
echo "vendored -> $DST ($(find "$DST" -name '*.py' | wc -l | tr -d ' ') py files, $(find "$DST" -name '*.yaml' | wc -l | tr -d ' ') yaml)"
