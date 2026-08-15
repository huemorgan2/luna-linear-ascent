#!/usr/bin/env bash
# Shrink the fight3d GLBs for the wire — run after every model export.
#
#   worldd/tools/optimize_glb.sh                # every GLB under static/site/fight3d
#   worldd/tools/optimize_glb.sh path/a.glb …   # just these, in place
#
# What it does (gltf-transform, no runtime decoders needed — three's
# GLTFLoader reads all of it natively):
#   • textures → 256px WebP (the scene renders through a 320x200 1-bit
#     shader; a 2048² JPEG is 90% of a Tripo GLB and invisible at that size)
#   • KHR_mesh_quantization (i16 positions/normals, u8 weights)
#   • animation resample (drops the constant keys Tripo bakes at 60 fps)
#   • weld / dedup / prune
# Typical result: 1.5 MB → 250–350 KB. Idempotent — running it twice on an
# already-shrunk file changes nothing.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/../static/site/fight3d"
if [ $# -gt 0 ]; then FILES=("$@"); else
  FILES=(); while IFS= read -r f; do FILES+=("$f"); done \
    < <(find "$ROOT/monsters" "$ROOT/players" -name '*.glb' | sort)
fi
GT="npx --yes -p @gltf-transform/cli@4 gltf-transform"
before=0; after=0
for f in "${FILES[@]}"; do
  b=$(stat -f %z "$f")
  tmp="${f%.glb}.opt.glb"
  $GT optimize "$f" "$tmp" --compress quantize --texture-size 256 \
      --texture-compress webp --simplify false >/dev/null 2>&1
  mv "$tmp" "$f"
  a=$(stat -f %z "$f")
  before=$((before+b)); after=$((after+a))
  printf '  %-52s %7d KB → %6d KB\n' "${f#$ROOT/}" $((b/1024)) $((a/1024))
done
printf 'total %d KB → %d KB\n' $((before/1024)) $((after/1024))
