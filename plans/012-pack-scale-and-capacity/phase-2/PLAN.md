# Phase 2 — engine: pack capacity, Forge upgrades, shop refusals

## Goal
A new character has 6 pack slots; the Forge sells 9/12/15/18-slot packs
gated at levels 3/6/9/12 for ◈ 40/120/300/600; every shop refuses to
open a new stack in a full pack before any gold moves.

## Steps
1. `economy.py`: `PACK_BASE_SLOTS = 6`, `PACK_TIERS = ((3, 9, 40),
   (6, 12, 120), (9, 15, 300), (12, 18, 600))`, `pack_next_tier(slots)`.
2. `state.py migrate`: `p.setdefault("pack_slots", PACK_BASE_SLOTS)`.
3. `core.py`: `pack_cap(p)`, `pack_used(p)`, `pack_can_take(p, slug)`,
   `_pack_full_refusal(p, scene_fn, what)`; call it in `_gear_purchase`
   (spare path + old-to-pack path), `_relic_buy`, `_medlab_buy`
   (inventory items only), `_basic_buy` (pack fallback path).
4. Forge: one `buy_pack` row (next tier or LOCKED w/ level; "your pack
   holds N" when maxed → no row, a line). `_forge_pack(p)` handler.
5. `_stamp`: `scene.pack_slots = pack_cap(p)`.
6. `unlocks.py`: four `Unlock("packN", "level", L, "opens", "a N-slot
   pack", "the Forge", ...)`.
7. `tests/test_012_pack.py`: default 6; refuse when full (medlab,
   relic, gear spare, gear old-to-pack); stacking allowed when full;
   Forge row locked below level 3, buys at 3 → 9 slots, refuses out of
   order; scene.pack_slots on the wire.

## Verification
`../worldd/.venv/bin/python -m pytest tests/ -q` — new file green, no
new failures elsewhere.

## Rollback
`git revert` the phase-2 commit; `pack_slots` keys left in player docs
are inert (unknown key).
