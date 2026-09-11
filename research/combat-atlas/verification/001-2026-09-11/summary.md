# Combat Atlas verification — run 001

Date: 11 September 2026 UTC. Environment: local vinext development server, Codex in-app browser; desktop1280×720 and mobile390×844. No connection to the live game. Source: Site commit `abff00d2a6419d083aebbdcb596641f1d03965a6`. Inspected plugin HEAD `2f9cfff5557cde824091e8e2ce9107171ba80024`; working tree left untouched.

| Scenario | Result | Evidence |
|---|---|---|
| Matchup and arrow conversion | PASS | Runestring/arcane: GroundPower139; AirPower32. Switching to ordinary on AirPower gives88 Power damage. |
| Blade reach | PASS | Ramguard against AirPower shows0 and explains no reach. Arithmetic grid also checks ground blades at noncontact distance. |
| Weapon details | PASS | Ramguard dialog shows0.85 attack,1.2 endurance,3-action cooldown,1.15 gold,1A:4B recipe and steadfast immunity. Compare button selects it. |
| Shield wall | PASS | D100/A40/S80: wall produces armor20, shield55, HP25, wear55. Shield0 produces HP80/wear0; shield300 retains HP25/wear55. |
| Knockback opening | PASS | “Land a shove” changes Contact to Far and explains the next bow/escape opportunity. |
| Upgrade endpoints | PASS | Used keyboard Home/End for all four grades; gates1/26/51/76 at+0. Runestring+20 costs81,422 /21,832,282 /17,351,742,687 /10,870,930,871,159. |
| Bestiary floor scaling | PASS | Floor100 preview changes HedgeRat to1,916,039,675,460 HP and885,159,086,190 ATK; explicitly proposed profile on neutral baseline. |
| Responsive navigation | PASS | At390px, sidebar opens and closes after selecting Weapons&arrows. Single-column weapon cards readable; wide tables scroll internally. Document width390px. |
| Art | PASS |24 visible image elements loaded in final desktop inspection; zero completed failed images. |
| Visual inspection | PASS | Read desktop matchup and phone matchup/arsenal screenshots captured inline in this task’s browser-tool outputs. |
| Build/typecheck | PASS | Final `npm run build` and `npx tsc --noEmit` exited0. |
| Authored source lint | PASS | `npx oxlint app lib` exited0. |
| Full scaffold lint | FAIL, inherited | Full `npm run lint` reports19 issues in unmodified generated components/hooks after fixing the five authored warnings. Vendored components were not edited. |
| Model checks | PASS |2,304 reach/channel combinations;146,400 shield allocations;84 upgrade states;100 neutral attack/floor comparisons with0 mismatches. |

The broad lint failure includes unused scaffold components and the generated mobile hook; it remains recorded, not suppressed. Dev hot updates while adding imports caused temporary module/hook errors; a full reload restored the page and the final interactive walkthrough ran successfully. One early mobile click occurred before hydration; the subsequent hydrated navigation passed. An initially reported unloaded lazy image was not a broken asset; final loaded-image checks passed.

These are artifact/model checks, not a production combat dojo. The proposed game mechanics, economic pacing and real-time multi-player warden behavior remain unimplemented and unverified. Publication status is recorded in ../../VALIDATION.md.
