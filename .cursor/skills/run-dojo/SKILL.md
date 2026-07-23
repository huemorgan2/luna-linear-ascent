---
name: run-dojo
description: >-
  Run Linear Ascent dojo end-to-end browser tests. Use when the user says
  "run dojo", "run dojo tests", "dojo style", or asks to test the game with
  real browser play. NEVER run only pytest — dojo tests always mean a real
  browser, a real Luna conversation playing the game, and screenshots you
  can read.
---

# Run Dojo — Linear Ascent E2E Browser Testing

## The rule

**Dojo = browser only.** When asked to run dojo tests, you MUST:

1. Open a real browser (use the cursor-ide-browser MCP tools)
2. Play a real game session with the actual Luna agent + plugin
3. Take screenshots at each key step and READ them
4. Verify server-side effects (plugin state / worldd DB) match what the UI showed
5. Write results to `dojo/results/<run-id>/` (repo root)

Running `pytest` alone is NOT a dojo run. pytest = plumbing (engine math,
StateBackend contract). Dojo = browser reality.

## Layer reference

| Layer | What | How | When |
|-------|------|-----|------|
| 1 | Engine math, contract tests | `pytest` (local backend AND worldd client) | CI — always green |
| 2 | worldd API driver | `curl` / scripted HMAC requests | After service changes |
| 3 | Browser screenshots | Browser MCP + read PNGs | After any card/UI change |
| **4** | **Multi-turn live play** | **Browser + real LLM** | **Any feature with state** |

**Dojo tests are Layers 3 and 4.**

## Before starting

1. **Reload the plugin on the QA Luna** — MANDATORY before every run. If tool
   descriptions or tool registration changed, **restart the Luna API**; tools
   only re-register on restart. This is the #1 cause of "nothing changed"
   false failures.
2. Confirm the QA Luna is serving (read the terminals folder for an existing
   `luna serve`; start one in background if missing) and that the `ascent_*`
   tools are registered.
3. worldd, if the scenario needs it (phase 3+):
   ```bash
   curl -s http://localhost:8600/health
   # if down:
   cd worldd && .venv/bin/uvicorn app.main:app --port 8600 --reload
   ```
   Confirm `"ok": true` before continuing. For solo scenarios the plugin's
   local `StateBackend` is enough — skip worldd.
4. If the QA Luna serves a built UI from `ui/dist/`, rebuild it after any UI
   change (`cd ui && npm run build` in the Luna checkout) — a stale bundle is
   the other classic false failure.
5. Decide player state: fresh character (wipe the test player's plugin
   state) vs. mid-game (record floor/gold/energy first so you can verify
   deltas).

## Running a dojo test plan

Test plans live at `plugin-linear-ascent/tests/<plan>/<test>.md` or
`worldd/tests/<plan>/<test>.md`. For each test:

1. **Read the plan** — understand the play session and expected outcomes
2. **Navigate** to the QA Luna chat
3. **Play the session** — send the chat turns, click options/cards, handle
   approval gates via the UI (never assume auto-approve)
4. **Screenshot every key state** — every scene card, meter change, death,
   vault visit
5. **Read every screenshot** — actually look at it and describe what you see
6. **Cross-check server truth** — after UI-visible effects, verify the
   ledger/state (plugin store or worldd DB) matches: gold deltas, energy
   spent, interest posted exactly once
7. **Write findings** — what passed, what failed, what looked wrong visually

## Output structure

```
dojo/results/<run-id>/
├── screenshots/
│   ├── 01-<name>.png
│   ├── 01-<name>.txt    (what you saw)
│   └── ...
└── summary.md           (findings, pass/fail, insights)
```

Run IDs follow the pattern: `<4-digit-number>-<feature>-<date>`
(e.g. `0003-vault-interest-2026-07-23`).

## Critical: always read the screenshots

Never report "it works" from code alone. After every screenshot:
- Use the Read tool on the PNG file
- Describe what you actually see
- Flag anything that looks wrong: raw JSON, broken card layout, missing
  1-bit banners, meters not moving, out-of-world prose, visual glitches

## What to look for beyond pass/fail

- **Tool discipline** — every state change has a tool call behind it (tool
  chip in the UI); the agent never narrates an outcome it didn't get from
  the engine
- **Option ordering** — the new scene's options replace the old ones; a
  stale option id must be refused with a steering hint
- **Meters** — ⚡/✦/HP bars move at the right moments, by the right amounts
- **Banners** — arrival moments render the full-bleed 1-bit banner, cache-
  busted (`?v=<manifest.version>`)
- **Voice** — in-world prose per the story bible; no "tool"/"plugin"/"state"
  leaking into the fiction
- **Timing** — more than 3 seconds between a choice and the next card is a
  finding

## Multi-turn / multi-tenant invariants (Layer 4 — always apply)

For any test spanning turns, days, or tenants:
- [ ] Choosing from an old scene after a new one rendered is refused
- [ ] Re-calling `ascent_scene` never mutates state (idempotent read)
- [ ] World-day effects (interest, regen, presents) apply **exactly once**,
      from server timestamps — retried turns must not double-pay (ledger
      idempotency keys)
- [ ] After page reload: the conversation shows the same game state; no
      ghost cards
- [ ] Cross-tenant (phase 3+): an event by tenant A shows for tenant B
      (happenings, Stone, inbox) with server-computed ages — clients never
      compute time

## When a server dies

macOS OOM-kills local servers frequently. If the QA Luna or worldd stops
responding:
```bash
# worldd
lsof -ti :8600 | xargs kill -9 2>/dev/null; sleep 2
cd worldd && .venv/bin/uvicorn app.main:app --port 8600 --reload
```
Restart the Luna serve process the same way (kill the port, start again) and
wait for its startup message before continuing the test.
