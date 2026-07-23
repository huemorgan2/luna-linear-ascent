---
name: dojo
description: >-
  Dojo testing philosophy and execution guide for Linear Ascent. Use when the
  user says "dojo test", "dojo style", "browser test", "test in production",
  or asks to verify the game's behavior through real browser play against a
  QA Luna (with plugin-linear-ascent loaded) or the live ascent-worldd.
---

# Dojo — Linear Ascent E2E Browser Testing

## Philosophy

A dojo is a place for practice and mastery. Linear Ascent dojo tests verify
the game through direct browser play — not coded assertions. An LLM agent
opens a browser on a running Luna, follows a script, plays the game, observes
the full page state, and makes a judgment call.

This catches things coded tests never will:
- A scene card that technically renders but reads out-of-world
- An agent that free-forms game state instead of calling `ascent_*` tools
- A numbered option list where typing "2" silently does nothing
- Meters that render but never move
- A flow that passes assertions but frustrates a real player

## When to use Dojo vs pytest

| What | Tool | When |
|------|------|------|
| Engine math (combat, interest, regen, death) | `pytest` | CI — always green |
| `StateBackend` contract (local AND worldd client) | `pytest` | CI + against a deployed worldd |
| Real browser, real cards, real play | **Dojo** | After any tool/engine/content/UI change |
| Multi-turn play, multi-tenant world | **Dojo** | Any feature with state |

**Dojo tests are never replaceable by pytest.** If someone says "just write a
unit test", that's a different concern — dojo tests verify the integrated
play experience. Plan 001 requires both: unit tests alone have missed
real-Luna bugs before.

## Test Plan Structure

Each test lives in `tests/<plan>/<scenario>.md` next to the plan's repo root
(`plugin-linear-ascent/tests/...` for game plans, `worldd/tests/...` for
service plans):

```
tests/
├── 001-buildfirst/
│   ├── README.md                 # Suite overview
│   ├── 01-character-creation.md
│   ├── 02-first-fight.md
│   └── ...
```

Each `.md` file contains:
1. **Preconditions** — player state, worldd up or not, content loaded
2. **Scenario** — step-by-step chat turns and clicks
3. **Expected Behavior** — described in human terms (cards, meters, voice)
4. **Fail Conditions** — specific anti-patterns (free-formed state, stale
   options accepted, out-of-world prose)
5. **Verify** — where to look: the chat UI, worldd DB/endpoints, ledgers

## Execution

Use the `cursor-ide-browser` MCP tools to:

1. Navigate to the target Luna (QA Luna locally, or a hosted tenant with the
   plugin installed for production runs)
2. Take screenshots at each key step
3. Read screenshots — actually look at them and describe what you see
4. Check DOM state via snapshots
5. Report pass/fail with evidence

### Production testing

For production tests:
- The world service is `https://ascent-worldd.onrender.com` — start with
  `GET /health` → `"ok": true` with server time.
- Play through a hosted Luna tenant that has the plugin installed.
- Multiplayer scenarios need two tenants — cross-tenant visibility (kills,
  happenings, letters, the Stone) is the thing to verify.

### Local testing

- worldd: `curl -s http://localhost:8600/health` (started via
  `cd worldd && .venv/bin/uvicorn app.main:app --port 8600 --reload`).
  Not needed for solo/pre-phase-3 scenarios — the plugin runs standalone on
  its local `StateBackend`.
- QA Luna: a local Luna checkout with `plugin_linear_ascent/` in its plugins
  directory; confirm the `ascent_*` tools registered.
- Approval gates: dojo runs must handle Luna approval cards and drive turns
  via the UI/API — never assume auto-approve.

## Critical Rule

**Never report "it works" from code alone.** After every screenshot:
- Read the PNG file
- Describe what you actually see
- Flag anything wrong: raw JSON in chat, broken cards, missing banners,
  frozen meters, error states, wrong elements

## Results

Write findings to the conversation. For formal runs, create:
```
dojo/results/<run-id>/
├── screenshots/
├── summary.md
```
(See the **run-dojo** skill for the full run procedure and output format.)
