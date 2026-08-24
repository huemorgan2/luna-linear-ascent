# figure3d — Labs 3D climber (071)

Isolated. Delete this folder to drop the experiment.

- `figure3d.js` — 1-bit portrait stage, idle breathe, hold grammar, hover tint
- `models/players/` — copies of the fight3d race rigs (human / elf / giant)
- `models/items/` — Tripo props through player level 10 + family fallbacks
- `tools/gen_items.py` — resumable Tripo generator
- `catalog.json` — slug → file / fallback / hold
- `test.html` — harness (serve `worldd/static/site`, open `/figure3d/test.html`)

Does not import `fight3d`. Flag: `p["labs"]["figure3d"]`.
