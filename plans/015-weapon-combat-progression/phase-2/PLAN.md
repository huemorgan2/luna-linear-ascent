# Phase 2 — Shared definitions and migration preparation

## Goal

Represent all weapon instances and monster traits without corrupting old saves. One definition must drive engine, cards and wiki. No player loses paid power or has several old copies collapsed into one.

## Steps

1. Define item instance IDs, family, grade,upgrade level, current/max endurance, effective progression floor, recipe version and conversion provenance. Preserve the ten equipment bands separately.
2. Define movement, defensive affinity, outgoing channel and traits independently. Import the64 approved art mappings and425 species records. The new three mauls must enter the canonical game asset distribution, including inventory-size assets.
3. Add versioned readers and migration previews for equipped/held gear, pack, faction storage, pawn/offers, gifts and pending rewards. Resolve instance ownership in local and HTTP backends. List every consumer, including PvP.
4. Add a planned `tools/progression/migrate.py` dry-run/report tool. Preserve legacy items when conversion cannot be fair; freeze death, condition, transfer and repair policy in its schema contract. Weapon honing remains only on unconverted legacy calculations.
5. Ensure old clients cannot mutate new instances through slug-only payloads. Produce an item-by-item reconciliation and rollback design before any live conversion.

## Verification

Run `python tools/progression/migrate.py --dry-run --fixtures tests/015-weapon-combat-progression/fixtures --report output/progression/migration.json` after creating the planned tool. Check every current weapon record, duplicated copies, all storage locations, hone/style/oil/wear extremes and missing optional fields. A second dry run produces the same mapping. Run dojo S02; both backends must pass the same inventory contracts.

## Rollback

Before enabling new writes, revert the adapters and keep original documents. After any new-format writes, retain compatibility readers and receipts; disable new mutations rather than restoring stale whole-player documents. Document exact compensating migration commands once the schema is implemented, before conversion is allowed.

## Operational notes

This is future work. Planned harness/tool paths named above must be implemented before their commands can run. Record exact implementation SHAs, deployed revisions and any migration arguments before executing a release or conversion. The plugin owns engine/content/cards; worldd owns authoritative shared state. Both inherit the versioned definitions. See the parent plan and DOJO-SCENARIOS.md.

## Execution status

Not started. This planning task does not claim runtime verification.
