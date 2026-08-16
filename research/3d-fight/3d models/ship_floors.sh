#!/usr/bin/env bash
# Copy every finished floor model into worldd/static/site/fight3d/monsters
# (50_walk.glb when rigged, 10_textured.glb for plan "none") and shrink it.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DST="$HERE/../../../worldd/static/site/fight3d/monsters"
todo=()
for d in "$HERE"/models/monsters/*/; do
  id=$(basename "$d")
  case "$id" in *_v[0-9]*|*_rig_v*) continue;; esac   # old floor-1 experiments
  src=""
  [ -f "$d/50_walk.glb" ] && src="$d/50_walk.glb"
  case "$id" in rust_seep|windfall_haunt|lamp_eater|hornet_swarm)   # plan none: unrigged, the scene slides them
    [ -z "$src" ] && [ -f "$d/10_textured.glb" ] && src="$d/10_textured.glb";; esac
  [ -z "$src" ] && continue
  if [ ! -f "$DST/$id.glb" ] || [ "$src" -nt "$DST/$id.glb" ] || [ "${1:-}" = "-f" ]; then
    cp "$src" "$DST/$id.glb"; todo+=("$DST/$id.glb"); echo "ship $id <- $(basename "$src")"
  fi
done
[ ${#todo[@]} -gt 0 ] && "$HERE/../../../worldd/tools/optimize_glb.sh" "${todo[@]}" || echo "nothing new"
