# 087 — preserve floor-2 contrast while reducing resolution

Status: planned 2026-09-11. This plan and its browser scenario are committed before implementation under the workspace devprocess.

## Problem

Roy compared the approved 1448×1086 floor-2 source with the shipped 492×369 map and identified lost tonal depth, especially in the lakes. The composition, scale, and labels are correct; the resolution conversion is not.

Measured on the exact saved source and shipped asset, using 24×24-pixel territory blocks at target scale:

- source local-tone range: `0.497`; shipped output: `0.410` (17.5% narrower)
- source local-tone standard deviation: `0.104`; shipped output: `0.076` (26.9% lower)
- source/output local-tone correlation: `0.980`, showing that geography survived while contrast compressed

The current output SHA-256 is `36c8e54a8a446eb4be147b52335db7c95b90342ca93d9009795066abd3294a61`.

## Root cause

The source already contains designed black-and-white dither. The generic map pipeline resizes it with LANCZOS, sharpens it, applies global autocontrast, applies gamma and a `0.85` highlight ceiling, then encodes it through another Bayer matrix. The second tonal remapping compresses region-scale density before the final one-bit grid is written. It protects thin edges but makes water, valleys, and lit slopes converge toward similar texture.

## Emergency mitigation

None. Production remains functional at version 0.111.0. This is a visual correction with no player-state or schema effect.

## Fix

1. [Phase 1](phase-1/PLAN.md): build measured floor-2-only conversion candidates from the approved source, inspect them at native and displayed scale, and select a tone-preserving recipe.
2. [Phase 2](phase-2/PLAN.md): update the repeatable converter and floor-2 asset, sync vendor, run coded and real-browser checks, version, release, and verify production if deployment remains authorized by the active map-release request.

## Verification

- Floor 2 remains exactly 492×369, opaque, and two-color: black plus `(217,217,211)`.
- Composition and HTML marker coordinates do not change.
- Territory-scale tone range is at least `0.470`, tone standard deviation at least `0.095`, and correlation with source at least `0.970`.
- Native-size visual review confirms the lower-left and mid-left water remain darker than adjacent lit ground while the tower, small houses, rails, fortress, and quarry edges remain readable.
- Floor-2 desktop and 320px browser screenshots show no chip/tooltip regression. A real Luna `show me floor 2` turn renders the corrected asset.
- Floor 1 and maps 3–10 remain byte-identical.

## Operational notes

- Work is isolated in parent/plugin branch `codex/087-map-contrast-preservation`; unrelated durability, admin, research, and lore work is untouched.
- Use the saved approved source at `worldd/plans/085-floor-maps-standard/art/sources/map_002_v1.png`; do not generate or redesign the map.
- Record every candidate formula and metric. The generic converter may gain an explicit tone-preserving mode, but existing map outputs must not be silently regenerated.
- Commit plugin first, then vendor/submodule pointer. Scan for secrets before every commit.

## Rollback

Revert the plugin asset/converter commit and parent vendor/pointer commit. This restores floor 2 byte-for-byte to SHA-256 `36c8e54a…4a61`; no data rollback is needed. If released, push the revert, run the explicit Render deploy, and verify version plus the restored asset hash.

## Execution status

Complete locally — 2026-09-11. Phase 1 selected direct BOX reduction and phase 2 integrated it as an explicit converter mode. Floor 2 now ships at SHA-256 `d5d46a03cc436ae3bbf7cd0365903b62a851529c9ee69ff0b05621d38b888f9e`; deployment evidence is recorded in phase 2.
