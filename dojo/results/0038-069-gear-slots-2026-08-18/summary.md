# DOJO 0038 — 069 slots, not pack: the gear map

- Date: 2026-08-18
- Plugin: d9609a6 (069 phases 1–5 committed: 885d519 e15de03 46a7a94 b7831fb 989ffd6; working tree = what 0.93.0 vendors); root 13e4fa4
- Environment: worldd local `uvicorn app.main:app --port 8779`, ASCENT_GAME_PATH=plugin-linear-ascent working tree, postgres localhost:5434/ascent_world, Chromium (playwright 1.50), viewport 1200×900 desktop + 390×844 mobile (S8)
- Scenario: `luna/dojo/tests/gear-slots/scenario.md`, runner `walkthrough.mjs`, seeds `seed.py`
- Account: dojo796672
- Result: **42/42 PASS**

| check | verdict | evidence |
|---|---|---|
| S1 signup | PASS | 200 dojo796672 |
| S1 seed fresh warrior | PASS | {"seeded":"web:dojo796672","profile":"fresh","level":1,"slots":1,"charm_slot":false,"gear":{"weapon":"rusted_sword","shi |
| S2 seven slots drawn | PASS | charm,armor,shoes,shield,weapon,weapon2,weapon3 |
| S2 left = charm/armour/boots, right = shield/w1/w2/w3 | PASS | charm,armor,shoes / shield,weapon,weapon2,weapon3 |
| S2 charm pouch locked, hover names level 9 | PASS | Locked — the charm pouch. School, level 9: 400 XP and a fee. Holds one charm or potion. |
| S2 weapon 2 locked with its unlock text | PASS | Locked — the second grip. School: 60 XP and ◈ 30. |
| S2 boots slot empty (dotted) with a hover | PASS | boots — none worn. Wear a pair from the pack; speed comes only from worn boots. |
| S2 armour filled, carries "Move to the pack" | PASS | [{"opt": "unequip_armor", "label": "Move to the pack", "hint": "the Gate-Issue Jerkin rides in the pack \u2014 it does n |
| S2 locked = dark grey box + lock glyph | PASS | {"bg":"rgb(34, 34, 34)","border":"solid 2px rgb(85, 85, 85)","mask":true} |
| S2 empty = dotted | PASS | dotted |
| S2 portrait stands between the columns at the column height | PASS | {"portrait":{"h":266,"w":133},"colH":266} |
| S2 no hand row / hcell left on the card | PASS | handrow=false |
| S2 hovering the locked pouch shows the unlock text | PASS | block/Locked — the charm pouch. School, level 9: 400 XP and a fee. Holds one charm or potion. |
| S3 pack boots offer "Wear" | PASS | COBBLED BOOTS / Wear / from your pack |
| S3 boots slot fills (left, third) | PASS | slot gm item act eq cobbled_boots |
| S3 SPD pips rise once worn | PASS | {"spd0":{"txt":"SPD 5"},"spd1":{"txt":"SPD 6"}} |
| S3 the boots left the pack grid | PASS |  |
| S3 worn boots offer "Move to the pack" | PASS | COBBLED BOOTS / Move to the pack / the Cobbled Boots rides in the pack — it does nothing there |
| S3 boots back in the pack, slot empty again, SPD back | PASS | SPD 5 |
| S3 the card says the pack piece does nothing | PASS | he Cobbled Boots goes to your pack — it does nothing there |
| S4 pack reads 6/6 | PASS | PACK 6/6 |
| S4 armour row still offered, hint says pack full | PASS | GATE-ISSUE JERKIN / Move to the pack / Pack full (6/6). Sell or drop something, or buy a bigger pack at the forge. |
| S4 refused in red with the count | PASS | toast=Can't move it — pack full (6/6) / shard= |
| S4 armour still worn, pack still 6/6 | PASS | slot gm item act eq |
| S5 level 8: charm pouch row present and locked (level 9) | PASS | {"opt":"buy_charm_slot","txt":"5 Unlock the charm pouch locked — level 9 (you: 8)","dis":true} |
| S5 clicking it under 9 refuses and names the level | PASS |  |
| S5 level 9: row open with the price | PASS | {"opt":"buy_charm_slot","txt":"5 Unlock the charm pouch 400 XP + 250","dis":false} |
| S5 bought: the card says so, pouch slot now dotted/empty | PASS | + POUCH — one charm or potion rides at your belt now. Set it from t / slot gm empty |
| S5 the row is gone once owned | PASS | train_blade,train_bow,train_staff,buy_carry2,back |
| S6 tonic in the PACK only: no drink row in the fight | PASS | close_in,stand,run,shield_wall |
| S6 mid-fight the pack tonic offers nothing (pouch-only, set before) | PASS | TROLLBLOOD TONIC / Nothing works from the pack — set it in your charm pouch and it will offer itself in the fight. |
| S6 out of the fight the pack tonic offers "Set in pouch" | PASS | TROLLBLOOD TONIC / Set in pouch / into the charm pouch |
| S6 tonic sits in the pouch, one left in the pack | PASS | trollblood_tonic |
| S6 with the tonic in the pouch the fight offers "Drink trollblood tonic" | PASS | close_in,stand,run,shield_wall,drink_tonic |
| S6 drunk: the pouch empties (the pack copy untouched) | PASS | slot gm empty |
| S7 two weapons in hand, lead marked gold, luck charm in the pouch | PASS | charm:luck_charm armor:gate_jerkin shoes: shield:gate_buckler weapon:rusted_sword weapon2:basic_bow weapon3: |
| S7 pouch tip names the charm pool | PASS | Luck charm — Luck charm — fortune leans your way while it sits in the charm pouch: the rare drop comes 25 points more of |
| S7 floor 6 with labs on: arena card | PASS | arena=true |
| S7 HUD shows the pouch under the climber HP | PASS | HP ▓▓▓▓▓▓▓░░░ 393/579 / ATK 37   DEF 33   SPEED 5 /  Luck charm  / ×12 |
| S7 attack tiles carry their own ATK | PASS | [{"opt":"attack","atk":"ATK 37"},{"opt":"attack_basic_bow","atk":"ATK 40"},{"opt":"stand","atk":""},{"opt":"run","atk":" |
| S8 390px: gear map fits, 48px slots, no horizontal overflow | PASS | {"gmW":227,"prW":332,"slot":48,"portraitH":214,"overflow":false,"cols":2} |
| V no console errors / page errors | PASS |  |

## Screenshots
01 gear map fresh · 02 pack boots menu · 03 boots worn · 04 armour menu, pack full · 05 refusal · 06 School level 8 locked · 07 pouch bought, empty · 08 fight, tonic in pack, no row · 09 tonic in pouch · 10 fight, drink row · 11 arena profile two weapons + charm · 12 arena HUD pouch + per-tile ATK · 13 mobile 390

## Regressions
None. Two runner fixes during the run (not product bugs): the arena HUD band exists only after the opener (check moved after the first strike); the arena seed hones the bow so the two attack tiles carry different ATK.
