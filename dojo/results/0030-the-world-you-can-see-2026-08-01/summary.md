# 0030 — the world you can see · 2026-08-01

Plan: `plugin-linear-ascent/plans/030-the-world-you-can-see/plan.md`
Stack: local render harness (`plugin-linear-ascent/tools/qa_030_shots.py`)
— the real engine (`core.apply_choice`) + the real legacy card
(`render.render_scene`) + Playwright at 720×1200 @2x, reduced-motion so
the typewriter paints whole. The full dojo stack (worldd + QA Luna)
needs Postgres, which this machine no longer has — worldd's `fallen_by`
was unit-verified instead; everything below is the vendored engine
surface, byte-identical to what worldd serves.

## Findings — PASS

- **Profile block** on every town/scene card: full-body 100×200 1-bit
  portrait left, HP/⚡/XP meters + LV/gold right, ATK/DEF as 10-icon
  pip rows (01). Level 1 warrior: ATK 8 → one full + one half sword,
  DEF 2 → one half armour; numerals always print beside the rows.
- **Portrait suits up with armour**: fresh climber wears rags (01);
  the same card with a Chain Hauberk equipped swaps to the chainmail
  figure and the pack strip names it (11). DEF 59 fills 10 half-steps
  across the row.
- **Morning Crier** (02): 1-bit newsprint 320×150 behind the text, ×
  close button top-right, census + condensed one-line warden report
  ("Warden Applewrath holds floor 3 at 43% — 2 blades against it"),
  two gossip lines, dawn note — all over the paper grain.
- **Vault strip** (03): 320×50 strongbox band over black with
  "DEPOSITED: ◈ 1,240" — coin glyph and amount in the same gold, same
  mask as the win card (unit-tested parity).
- **Painted amounts everywhere**: gold ◈, ⚡ energy, XP each one
  colour for icon + number (01, 02, 03, 11).
- **Gate floor tiles** (05): each open floor is a tall row — fields
  photo + violet warden photo side by side, name and biome right; the
  war line above ("the war is on floor 3 — the Warden stands at 43%").
- **Arrival reel** (06 → 07 → 08): first entry to a floor plays beat I
  (the world — eyebrow "FLOOR 1 · THE FENCEROWS · I", NPC voice
  quoted) then beat II (the Warden, violet) then the arrival card;
  single [1] Next option each beat; any stray click just advances.
  Plays once per floor (`floor_seen_1` flag) — re-entry goes straight
  to the floor card.
- **Fallen keep beat** (14): floor 2's beat II reads "Warden Sedgeback
  has already fallen … Broken by Brand, Okko." — the slayer names ride
  worldd's new `fallen_by` map.
- **Enemy plate** (10): ATK/DEF pip rows + HP bar + range chip pinned
  top-right over the wolf art, player-style icons; dossier body gives
  the story line and "You — ATK 8 … DEF 2" comparison; drops (coin
  range, XP, drop-chance bullets) ride `scene.enemy["drops"]` and the
  [i] dossier (unit-tested to_text parity).
- **NPC voices** (04, 09): lodge keeper rotates tellings; floor NPC
  greets on the reel and talks on the floor — warn line + warden ATK
  numbers match the schema.
- **Level ~10 spot-check** (11, 12, 13): frontier 10, chain portrait,
  ATK 35 / DEF 59 rows, gate lists nine floors below the war floor,
  floor-9 fight plate renders the same way.

## Notes

- Screenshots 01–14 in `screenshots/`; the harness is reusable
  (`tools/qa_030_shots.py <out_dir>`).
- Floor-reel GIF loops (floor{1..10}_world/_warden + warden_fall,
  Veo 3.1 → 1-bit) land in `content/art/events/`; the reel falls back
  to still banners where a loop is missing — floors 11+ by design.
- Full pytest suite: 753 passed, 1 skipped, ~5s (bestiary floors
  11–100 self-skip behind `ASCENT_FULL_SIMS=1` — 030 Phase 9).
- worldd DB-backed tests not runnable on this machine (no Postgres);
  `fallen_by` verified by pure-function unit run + this harness's
  synthesized world payload.
