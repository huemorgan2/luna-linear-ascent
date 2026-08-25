# 080 scenario — finisher gear parity (phase 3: your gear, your kill)

## Preconditions

- Local worldd on :8600, phase 3 deployed locally (server payload + fight
  dressing).
- Harness extended to pass a `worn`/`paths` spec (mirroring data-kill3d).

## Scenario

1. Open the finisher harness with a spec wearing `iron_sword` (weapon),
   `gate_buckler` (shield), `boarhide_jack` (armor), `cobbled_boots`
   (shoes), race human, vs grey_wolf.
2. Screenshot approach, strike, aftermath; zoom-crop the climber.
3. Repeat with race elf + a bow lead (`ashwood_bow`), and race giant + a
   staff lead (`coalglass_staff`).
4. Repeat once with a bogus worn slug (`no_such_item`).
5. In-game check (the "first user query"): play a wilds fight to a kill on
   /play with a geared tenant, watch the real victory card's finisher.

## Expected behavior

- The climber carries the REAL models: the same sword/shield/armor
  silhouettes the portrait shows for those slugs — not the old generic
  blade.
- Gear rides its bones through gait and strike: shield stays on the
  forearm, armor on the torso, nothing floats or lags.
- The strike still reads: blade sweeps with the arm, impact lands.
- Bogus slug degrades to the family GLB, sequence still plays.
- The real victory card in /play mounts the dressed finisher (payload made
  it through combat.py → render.py → data-kill3d).

## Fail conditions

- Generic placeholder weapon appears for a geared climber.
- Any worn piece detached from its bone, inside the body, or oversized.
- Sequence stalls or degrades to GIF because of a gear 404.
- data-kill3d payload missing worn/paths on a geared kill.

## Verify

- Network tab: item GLBs fetched from `/static/site/lib/models/items/…`,
  warmed BEFORE the kill card where `data-rig3d` carried them.
- Plugin `pytest tests/test_kill3d.py -q` green (new payload fields).
- DB/state untouched: gear payload is read-only presentation.
