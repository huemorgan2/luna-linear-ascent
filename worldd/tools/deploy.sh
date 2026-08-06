#!/usr/bin/env bash
# Deploy worldd to Render and wait until the new code is actually serving.
#
#   worldd/tools/deploy.sh            # deploy origin/main, poll, verify
#   worldd/tools/deploy.sh --check    # report live version + last deploy only
#
# Why this exists: ascent-worldd has autoDeploy=yes, but GitHub has never
# notified Render for this repo (no webhook, and the Render GitHub App has
# no access) — every deploy in the service's history is trigger=api. A push
# to main therefore ships NOTHING on its own. Between Aug 2 and Aug 5 that
# silently left two released versions unshipped while players ran old code.
# Until the repo connection is repaired in the Render dashboard, this script
# IS the deploy step. Run it after every push that should reach players.
#
# Auth: RENDER_API_KEY, or the render CLI's own key (~/.render/cli.yaml).
set -euo pipefail

SERVICE="${ASCENT_RENDER_SERVICE:-srv-d9ha3csvikkc73ff5rg0}"   # ascent-worldd
HEALTH="${ASCENT_HEALTH_URL:-https://ascent-worldd.onrender.com/health}"
API="https://api.render.com/v1"

KEY="${RENDER_API_KEY:-}"
if [ -z "$KEY" ] && [ -f "$HOME/.render/cli.yaml" ]; then
  KEY=$(sed -n 's/.*key: \(rnd_[A-Za-z0-9]*\).*/\1/p' "$HOME/.render/cli.yaml" | head -1)
fi
[ -n "$KEY" ] || { echo "! no RENDER_API_KEY and no ~/.render/cli.yaml" >&2; exit 2; }
auth=(-H "Authorization: Bearer $KEY")

live_version() { curl -fsS "$HEALTH" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("game","?"))'; }

if [ "${1:-}" = "--check" ]; then
  echo "live version : $(live_version)"
  curl -fsS "${auth[@]}" "$API/services/$SERVICE/deploys?limit=1" | python3 -c '
import json,sys
d=json.load(sys.stdin)[0]["deploy"]; c=d.get("commit") or {}
print("last deploy  :", d["status"], d.get("finishedAt","")[:19], (c.get("id") or "")[:8], "trigger="+str(d.get("trigger")))
print("commit       :", (c.get("message") or "").splitlines()[0][:70])'
  exit 0
fi

# The vendored engine is what worldd actually imports, so a stale vendor
# ships old game code under a new version number. Catch it before Render does.
want=$(sed -n 's/.*"\(.*\)".*/\1/p' "$(dirname "$0")/../vendor/plugin_linear_ascent/version.py")
src=$(sed -n 's/.*"\(.*\)".*/\1/p' "$(dirname "$0")/../../plugin-linear-ascent/plugin_linear_ascent/version.py" 2>/dev/null || echo "$want")
if [ "$want" != "$src" ]; then
  echo "! vendor is $want but the plugin is $src — run worldd/tools/vendor_game.sh first" >&2
  exit 3
fi

echo "→ deploying $SERVICE (target version $want, live now $(live_version))"
dep=$(curl -fsS -X POST "${auth[@]}" -H 'content-type: application/json' \
        -d '{"clearCache":"do_not_clear"}' "$API/services/$SERVICE/deploys" \
      | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
echo "  deploy $dep"

for _ in $(seq 1 60); do
  st=$(curl -fsS "${auth[@]}" "$API/services/$SERVICE/deploys/$dep" \
       | python3 -c 'import json,sys;print(json.load(sys.stdin)["status"])')
  printf '  %s\n' "$st"
  case "$st" in
    live) break ;;
    build_failed|update_failed|canceled|pre_deploy_failed)
      echo "! deploy $st" >&2; exit 1 ;;
  esac
  sleep 15
done
[ "$st" = "live" ] || { echo "! deploy did not go live in time" >&2; exit 1; }

# Render keeps the old instance serving through the swap, so /health can
# still answer with the previous build for a few seconds after "live".
for _ in $(seq 1 12); do
  got=$(live_version || echo "?")
  [ "$got" = "$want" ] && { echo "✓ live: $got"; exit 0; }
  sleep 5
done
echo "! deploy is live but /health still reports $got (wanted $want)" >&2
exit 1
