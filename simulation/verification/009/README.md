# Prepared combat and resource experiments

Run from the repository root with `ASCENT_GAME_PATH=$PWD/plugin-linear-ascent` and the project Python environment:

```
python simulation/verification/009/site_returns.py --seeds 2 --site drowned-copse --out simulation/verification/009/sites-canary.json
python simulation/verification/009/weapon_niches.py --seeds 1 --anchor 3 --family viper --out simulation/verification/009/weapons-canary.json
python simulation/verification/009/site_returns.py --seeds 32 --out simulation/verification/009/site-results.json
python simulation/verification/009/weapon_niches.py --seeds 8 --out simulation/verification/009/weapon-results.json
python simulation/verification/009/site_returns.py --seeds 2 --site fallen-star-crater --honed --out simulation/verification/009/sites-honed-canary.json
python simulation/verification/009/site_returns.py --seeds 32 --honed --out simulation/verification/009/site-honed-results.json
```

These are endowed test characters, not days-to-progress evidence. Exact fixture state accompanies every result. Weapon level is the greatest canonical +0–20 rank whose floor requirement is met; grade follows the current floor. Character level is `max(3,min(30,floor−5))`, all training ranks6. Defenses are the strongest actual available Forge offers at those access levels.100 ordinary grade-matched arrows, full initial condition/HP and20energy. No subsequent free supplies/healing. A site trial carries its tool price plus100same-floor income units in gold; buying the tool, deaths and other real costs count in netgold. No claims are discarded; a full pack with a waiting weapon claim ends a route trial.

The technique comparison deliberately isolates one family against a repeated two-creature real roster. It measures survival/control/action advantages and blind spots, not the optimal three-weapon deck. All damage, status, RNG, wear, rewards and settlement run through the game core. A family with no improvement is a finding to investigate, not evidence to suppress. Different specimen variety, tactical policies and natural affordability are separate phase5 work.

The optional `--honed` comparison adds the canonical reference hone to armor/shield before initial HP. This is a declared prepared investment, not free honing during a route. Earlier outputs retain their un-honed fixture and are never overwritten by the comparison. The first late-floor death findings and pre-execution rationale are in phase4/DEFENSE-COMPARISON.md.

All output includes an engine source hash and rejects changes during execution. Initial results:

| Site floor / target | Gather / hunt target return, un-honed | Same ratio, reference-honed defense | Gather deaths with honing /32 |
|---|---:|---:|---:|
|3 Wood|2.77×|2.77×|0|
|3 Raw Metal|1.92×|1.92×|0|
|18 Steel|62.94×|28.64×|0|
|25 Hardwood|12.56×|13.67×|15|
|45 Starforged Steel|25.46×|16.33×|3|
|55 Meteorite|10.15×|10.79×|9|
|70 Shard Matter|19.67×|15.48×|0|
|80 Mythic Threads|undefined: hunters secured zero|5.09×|1|

These are ratios of secured material divided by paid energy across32trials, including deaths and attempted escapes. High ratios at18/25/45 partly reflect early access to the next grade's resource and low hunting drop rates; they do not imply comparable gold profit. Every trip includes a newly bought tool, so netgold is not amortized long-term ROI. In the honed comparison floor70 hunter deaths fall30→2 and gatherer deaths13→0; floor80 falls24→2 and20→1. Floor25/45/55 still expose weak preparation/strategy and require further investigation. These small conditional samples do not certify sustainable progression.

The weapon matrix contains11,776 actual two-creature fights (736 per family). Technique vs plain wins: Recoil297/229, Repulsor227/169, Stormbell180/168, Thunder142/138, Viper141/138, Briar144/142. Others sometimes improve action count/HP without changing wins. Breach/Skirmisher/Runestring are passive or ammo-specific; Ramguard needs bow switching/escape and Frostbind needs pursuit-sensitive preparation. Their zero isolated technique improvement is not proof of a defect or a useful niche. Targeted complementary checks remain required.
