# Dojo run 0005 — XP economy (plan 006)

Stack: QA Luna (`luna/` submodule, :8777, fresh `luna_ascent` DB), plugin
0.6.0 via symlink, local StateBackend (solo — no worldd needed for these
scenarios). Fresh character: **Sylvara, elf sorcerer**. Driver: own headless
Chromium (`drive.py`) after the shared Playwright browser kept losing tab
focus to the user's live session.

## Scenario results (tests/006-xp-economy/)

### 01 — ✦ meter is XP, philtre gone — PASS
- Roothollow arrival: `✦ 0/60` with an empty block bar; no regen meter.
- After first kill: `+ 16 experience` (12 base ± jitter × 1.05 elf) →
  `✦ 16/60`, 3 blocks filled. (03/09-victory screenshots)
- Medlab: 6 items, **no Aether philtre**. (04-medlab)
- Character sheet: `✦ Aether 7/60` (xp/xp_need), no mana row. (13-sheet)
- Text fallback ("1"/"2") worked at every step.

### 02 — hone charges gold AND XP — PASS
- Hint renders the dual price: `Hone Pigsticker +1 — ◈ 86 + ✦ 18`.
- With ✦ 7: refusal "The bench takes ✦ 18 of what you've learned along
  with the coin — you carry ✦ 7. Hunt first." Gold NOT charged. (20)
- With ✦ 50: success `− ✦ 18`, gold −86, bench shows `weapon +1`. (21/22)

### 03 — levels gate gear and floors — PASS
- Tier-2 forge at level 1: every row hints `· level 11`, body line "tier 2
  steel answers to level 11 hands"; buying Wolfbite refused, ◈ 100,000
  untouched. (23/24)
- Floor 13 at level 1 (frontier 13): refused — "Level 3 minimum for floor
  13" — with a real ascent_choose call behind it. (26)
- Warden unlock gate unchanged: floor 12 absent from the gate list until
  frontier moved. (25)

### 04 — Sleep and scan burn experience — PASS
- Fight card: `Sleep spell — class · ✦ 12`, `Ask the shard to scan it — ✦ 6`
  (0 optics charges → XP fallback price shown). (06)
- Sleep at ✦ 0: refused, fight alive, pool intact; Luna relayed the price.
  (07)
- Scan from pool: ✦ 16 → 10, stat line printed. (10)
- Sleep at ✦ 19: fight skipped, `− ✦ 12 experience burned — you step past
  it`, **no XP award**, pool → 7. (12)

## Bonus paths exercised
- **Death save**: warden fight at 1 HP → shardmind pull-out, gold intact.
- **Real death (beginner mercy)**: −◈ 5,000 (half), gear survived, bank
  untouched — and **✦ pool + level untouched by death**. (18-forge)
- Idempotent `ascent_scene`: repeated reads, meters unchanged. (14)

## Findings & fixes during the run
1. **Agent said "mana"** when relaying the first Sleep refusal (engine text
   was clean). Fixed in `plugin.py` `_SHARED_RULES`: METERS paragraph — no
   mana exists; ✦ is crystallized experience with its exact mechanics.
   After restart the agent consistently used ✦ ("cost us 12 ✦"). 
2. `version.py` still said 0.5.0 while the manifest said 0.6.0 — synced.
3. Not a bug, QA note: editing `unlocked_floor` mid-scene reshuffles
   after-fight option numbering (a "gate" option appears) — bare-number
   replies sent blind then land on the wrong option. Engine validated every
   transition correctly throughout.

Regressions found: none.
Out-of-world moments: the single "mana" slip (fixed, re-verified).
Verdict: ship it.
