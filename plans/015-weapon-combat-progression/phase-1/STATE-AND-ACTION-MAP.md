# Runtime contracts and ownership audit

13 September 2026. Integrated root `1f45fb1`, plugin `553500f`, vendored engine0.112.0. This is the last legacy baseline; these are implementation contracts, not claims that the changes exist.

| Consumer | Existing representation / behavior | Candidate representation / action |
|---|---|---|
| `state.new_player`, `ensure_current` | version11; one held slug; one durability entry per slug; School grants slots | explicit rules revision; three cells referring to owned instance IDs; monotonic item sequence; conversion receipts |
| `core.current_scene`, `apply_choice` | builds location scene and validates options; global pack actions precede location dispatch | same public entry points; enforce encounter/expedition ownership locks before global actions; stale scene refused at host and transaction boundary |
| School | `buy_carry2`, `buy_carry3`; training and mastery separate | remove only carry purchases; preserve training, mastery, charm pouch; exact recorded refunds, capped historical fallback |
| Pack / loadout / profile | slug counts, `held`, gear lead pointer; profile reads public slots | instance collection, three selected IDs and explicit active ID; no duplicate ID or fourth weapon; other player's sheet stays read-only |
| Forge / repair / hone | tiered slug purchase, per-slug hone, durability pools | source-specific grade/level/condition; two-material recipe and gold quote; one atomic upgrade; compatibility for unconverted legacy gear |
| Hunt / deep hunt | one draw, entry energy, immediate kill gold and XP clipped to bar | persisted ordered offer; one energy only when each enemy begins; immediate reserved XP; pending haul secured only on complete victory |
| Combat | selected slug resolves through old triangle; absolute shield block | selected instance, affinity plus movement, gap and phase effects; shield leakage and absorbed-share wear; structured resistance event |
| Death / retreat / revive | clears old encounter, may destroy gear; separate rescue effects | lose current haul on abandon/death; keep prior secured resources and weapon levels; in-place revival keeps group receipts |
| Daily clock / sleep | dawn restores HP; active sleep heals over time | no dawn/sleep healing inside committed group or expedition; energy clock remains real and exhaustion latched per enemy |
| Contracts / weekly / assist / social | kill effects can independently grant loot | distinguish immediate kill XP from secured completion accounting; forbid partial-haul cashout through another consumer |
| Storage / pawn / gifts / faction / PvP | slug-based equipment references | conversion inventory includes every ownership location; unresolved legacy assets retain functional compatibility and cannot be minted twice |
| Gathering | absent | utility tool outside deck; persisted expedition haul; paid gather attempts and separate paid ambush enemies; explicit safe extraction receipt |
| Vault | five 1% slices/day, collect into principal | retain actual clock and interest implementation; policy weighs reserves and upgrades against investment |
| Ordinary wardens | free entry; three energy each swing; shared damage published after private exchange; delayed healing/pity | phase6 immediate authoritative damage with continuous healing and shared cadence; finite energy; preserve/reconcile old wounds |
| Milestone wardens / floor100 | five energy pledge, asynchronous power quorum | same concurrent HP/healing law as other wardens; no banked future damage |
| HTTP / local persistence | same core; worldd saves doc/ledger/effects in transaction | same core and versioned docs; duplicate request and stale scene checked after ownership row lock; no repeated charge or settlement |
| Simulator / wiki | actual imported vendor, but old mechanics; wiki proposal data separate | engine owns published rule catalog; simulator chooses legal actions only; candidate rules revision is part of every run fingerprint |

## Candidate boundary and compatibility

`ASCENT_RULESET=collection-v1` is an explicit isolated QA switch during implementation. Existing active legacy encounters finish under legacy rules before conversion. Converted saves remain readable regardless of environment switch; disabling new enrollment must not strip their instances, XP reserve or unsettled haul. No production conversion is authorized by a QA flag. Conversion preview operates on copies; apply uses stable receipts and keeps provenance. Source and vendor will advance together before QA changes rules.

The grade catalog and425 creature identities currently displayed in the wiki become engine-owned content. Export/copy the authored settings once, then generate wiki views from that source. Do not import generated site JSON from the game or duplicate combat formulas in the simulator.

## Warden energy decision

Keep three energy per accepted damaging action for the first concurrent-warden experiment; entering/looking is free in that candidate. Use one shared per-player action timestamp and a six-second minimum interval, including multiple clients. This is a candidate to test against finite energy and real shared healing, not a claim about required party sizes. Measured legacy entry is already free and damaging swings cost three energy; milestones use five-energy pledges. The unused entry-cost constant must not be mistaken for an actual charge. Ordinary-group exhaustion does not authorize free warden swings.

## Reversibility

No production documents were changed. Baseline integration rolls back with `git revert -m 1 1f45fb1` in the root and `git revert -m 1 553500f` in the plugin if needed. Subsequent schema readers must remain until all candidate groups/expeditions are settled; never restore a pre-migration player snapshot over later earnings.
