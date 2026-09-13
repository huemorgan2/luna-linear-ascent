# Candidate opening run — actual game0.114.0

Integration evidence, not final balance approval. Eight players,10 days,4 workers,4 readiness trials. Source/plugin18a3956; root4f58d81 contains the recorded engine and runner hashes. The raw run was generated while that parent commit was being prepared, so its historical `code_commit` field precedes the containing commit. Both exact content hashes match the committed code.

Engine hash: `7bab3e04291452164204930b54069ab6775f9b57757aadcd2f1f907c749ee436`.
Runner hash: `6622464afbc3c950eba7c15eeb3f7151511a74275e11df9164893e62c9aa2767`.
Runtime: 15.9706 seconds. Both captured player traces replayed exactly.

| Floor | Players capable | Fastest observed day | Population median day |
|---|---:|---:|---:|
| 1 | 8/8 | 0.0 | 0.0 |
| 2 | 8/8 | 0.0 | 0.0 |
| 3 | 8/8 | 0.0 | 0.0 |
| 4 | 8/8 | 0.334 | 1.0 |
| 5 | 8/8 | 0.334 | 1.0 |
| 6 | 8/8 | 1.335 | 1.668 |
| 7 | 6/8 | 3.001 | 3.667 |
| 8 | 6/8 | 4.0 | 4.0 |
| 9 | 2/8 | 9.0 | Not reached by half |
| 10 | 0/8 | Not reached | Not reached by half |

First3 floors can already be cleared with the authored starting deck. This is a real capability result; it is not three floors of world unlock progress. Later timing remains slower than the intended envelope. Cautious policies had fewer deaths; mining/Forge advantages and Vault compounding require larger controlled experiments in phase5.

Source selection is explicit (`collection-v1`). These are complete group wins. Every outcome, reward, payment, repair and extraction came from the game library; only choices, attendance, virtual time and the documented frontier/probe fixtures belong to the simulator.

Verification:232 server tests passed;1480 plugin tests passed with8 known legacy failures,4 skips and1 xfail. Two new CSS regressions were fixed before the follow-up. All62 simulator tests passed; separate candidate automatic-CPU parity and replay checks passed. Browser evidence is still in progress.
