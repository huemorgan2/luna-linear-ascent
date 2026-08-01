# 031 punch list — QA pass (2026-08-01, v0.37.0)

Real engine + real renderer via `tools/qa_031_shots.py`, Playwright
720×1200 @2x, reduced motion. One shot per punch item.

| shot | items | verdict |
|---|---|---|
| 01-town-ident-pack-paper | §1 §3 §4 §12 | no left stripes anywhere; ident band (name + ELF ARCHER left, bold LEVEL 5 / COINS ◎ 1,234 right); pack is a slot grid with promoted IN HAND / SHIELD boxes and empty Minecraft-style spaces; the Morning Crier reads as a newspaper — double-rule masthead, serif headline, dotted item rules, ✕ to close |
| 02-forge-card-wall | §14 | the Forge is a card wall: big 1-bit icons, price + stat hints in gold, [i] kept on every card corner, locked rungs dimmed with 🔒 gate; hone/repair/back stay rows below; zero prose between headline and racks |
| 03-lodge-evening | §10 §11 | options read "ACTIVITY: rest by the fire" and "JOB OFFER: the palisade watch — ◎ 38 at dawn — paid work, no rested-XP bonus"; below the options the filled, outline-free violet band: "ACTIVITY IN THE LODGE: no activity selected" |
| 04-wick-talk | §9 | Wick's portrait floats left of the text with his name under it; he explains the lodge plainly, quotes tonight's shift and pay, then bores you with his elbows |
| 05-gate-floor-list-plain | §13 | the floor list carries no art — plain rows again |
| 06-infloor-hunt-vs-keep | §13 §5 | fields art on "Hunt the wilds", warden art on "The Warden's keep — Warden Brackjaw · 3 ⚡ a swing"; walking in is free, the swing carries the tax |
| 07-warden-keep | §5 §6 | keep scene; the Warden [i] dossier lists coin and XP drop ranges like every monster |
| 08-archer-at-range | §7 | archer opens at range; the dossier says the monster CANNOT reach you while crossing; no free hits drawn by shooting |
| 09-death-pays-the-tax | §8 | level-1 death: "− ◎ 450 carried gold, scattered where you fell" (half of 900 carried); past level 6 the pardon ends (90% + a pack stack, registered as the "pardon_ends" unlock) |

Engine gates: full pytest 768 passed / 1 skipped; ASCENT_FULL_SIMS
bestiary + retune + damage-type gates all green. Reference archer now
wears rack boots (speed is orthogonal to the ATK/DEF tuning reference);
prey that matches the archer's stride gates at ≥75%, the floors-1-10
danger bar moved 80→85 to price §8's dearer deaths.
