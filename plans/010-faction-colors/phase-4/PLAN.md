# Phase 4 — vendor, migrate, deploy, walk the dojo

## Goal

Production serves the new engine from BOTH homes (worldd vendor +
marketplace plugin), the migration is live, and a dojo walkthrough
proves every asked-for behavior with screenshots. Measurable:
`/health` game field reports 0.86.0 on both surfaces; dojo run folder
with PASS on all five checks.

## Steps

1. Bump `plugin_linear_ascent/version.py` → `0.86.0`; plugin full
   pytest.
2. `worldd/tools/vendor_game.sh` — sync the vendor copy; worldd full
   pytest (`deploy.sh` refuses a stale vendor, but verify the version
   match by hand too).
3. Apply `020_faction_colors.sql` to the production DB **before** the
   code deploy (additive + default ⇒ old code runs fine on the new
   schema; the reverse order would 500 on the new SELECTs). Snapshot
   the DB first, per fleet-op rule.
4. Deploy per the production workflow (push, trigger via API, poll to
   live). Canary check: one authenticated card render before calling
   the fleet good.
5. **Dojo scenario** `luna/dojo/tests/faction-colors/` (scenario.md +
   walkthrough.mjs), results into the next numbered `dojo/results/`
   folder. Production probes use the UA header and fresh isolated
   browser contexts.

## Dojo scenario (summary — full text ships in the scenario file)

- **Preconditions**: one pre-plan faction (no color ever chosen); a
  level-4+ climber with ◈ 500+ who belongs to no faction; a steward
  account of a second faction.
- **Scenario / expected**:
  1. Found a faction; the flow asks name → banner → **color** and
     shows 9 named swatches (Mouse Grey … Root Brown); pick Ember Red.
  2. On the card, hover the strip's banner+name: the area behind
     exactly the banner and the name fills `#f26541`, ink flips black.
  3. Measure the sigil box hovered vs not: identical size (no growth);
     sigil pixels are chunky (160×56 source).
  4. The `N climbers / N online now` block shows no background change
     on hover.
  5. As steward, open the admin desk: a color row sits in the same
     panel as rename; change to Aether Teal; another member's card
     hover now shows `#45d0c0`.
  6. The legacy faction's strip hovers Warden Violet `#d967c8` — the
     fallback, not blank, not black.
- **Fail conditions**: any transform/growth on hover; hover coloring
  the counts or the whole strip row; a 10th color or a hex outside the
  palette; legacy faction rendering with no ink.
- **Verify beyond UI**: `SELECT name, color FROM ascent_factions` shows
  the founded row `ember-red`, the recolored row `aether-teal`, the
  legacy row `warden-violet`; server logs clean of 4xx/5xx on
  `/v1/faction/recolor`.

## Verification

- `/health` game field: 0.86.0 on worldd AND on the marketplace plugin
  deployment (scene vs render split — both must be live).
- Dojo results folder committed: summary.md (date, SHAs, environment),
  PASS/FAIL table, screenshots. Regressions filed, not quietly fixed.
- Append Execution status to every phase PLAN.md; commit.

## Rollback

Redeploy the previous release (previous vendor commit). The color
column stays — additive and default-filled, harmless to old code. If
the migration itself must go: phase-1 rollback SQL after the code
rollback.

## Execution status

_(appended after execution)_
