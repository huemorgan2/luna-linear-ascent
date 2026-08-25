# figure3d — Labs 3D climber (071)

Isolated. Delete this folder to drop the experiment (the shared `../lib/`
stays — fight3d uses it too).

- `figure3d.js` — 1-bit portrait stage, idle breathe, hover tint
- `models/<slug>/00_base.glb` — raw Tripo sources the generator resumes from
- `tools/gen_items.py` — resumable Tripo generator; writes finished items
  to `../lib/models/items/`
- `catalog.json` — slug → file / fallback / hold
- `test.html` — harness (serve `worldd/static/site`, open `/figure3d/test.html`)

Does not import `fight3d`. Placement comes from `../lib/sockets.js`
(plan 079 — named sockets + grip table); loading, body normalization and
the dressing loop from `../lib/character.js`, and every runtime GLB from
`../lib/models/` (plan 080 — one rig pipeline for both 3D scenes).
Flag: `p["labs"]["figure3d"]`.
