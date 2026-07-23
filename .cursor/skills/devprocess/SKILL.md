---
name: devprocess
description: >-
  Standard dev process for executing Linear Ascent plans — branch (plugin
  submodule vs worldd), test, build, verify. Use whenever executing a plan
  from plugin-linear-ascent/plans/ or worldd/plans/.
---

# Dev Process — Linear Ascent

## ⛔ CRITICAL — DATA PRESERVATION

**NEVER delete, drop, or destroy production data. EVER.** This applies to the
`ascent-world-db` Postgres on Render and to any player state.

When writing migrations, schema changes, or any code that touches existing data:
- **ALWAYS migrate and preserve existing data** — transform, move, or archive it.
- **NEVER use `DROP TABLE`, `DELETE FROM`, or `DROP COLUMN`** on tables/columns
  that contain player data without first copying that data to its new home
  **and verifying the copy succeeded**.
- The `ledger` table is append-only by design — never rewrite it.
- If renaming or restructuring, keep the old column/table until the migration
  is verified in production.
- **When in doubt, keep the data.** Storage is cheap. A player's lost character
  is irreplaceable trust.

This rule is non-negotiable. Violating it is a production incident.

---

## Repo layout — know where you are

This project is TWO git repos:

| Path | Repo | What lives here |
|---|---|---|
| `.` (root) | `luna-linear-ascent` | `worldd/` service, `render.yaml`, README |
| `plugin-linear-ascent/` | **git submodule** → `huemorgan2/plugin-linear-ascent` | the game plugin: vision, design, content, plans 001/002, plugin code |

Plans live at `plugin-linear-ascent/plans/XXX-name/plan.md` (game) and
`worldd/plans/XXX-name/plan.md` (service). Work on the plugin happens **inside
the submodule**; after committing there, bump the submodule pointer in the
parent repo as a separate commit.

## 1. Branch

Create (or switch to) a branch matching the plan folder name — **in the repo
that owns the plan**:

```bash
# plugin plan → branch inside the submodule
cd plugin-linear-ascent && git checkout -b XXX-name

# worldd plan → branch in the parent repo
git checkout -b XXX-name
```

Branch name, plan folder, and test folder share the same name.

## 2. Write E2E Test Scenarios First

Create `tests/XXX-name/` (next to the plan's repo root) with **scenario files**
(`.md`) **before** writing implementation. These are NOT coded assertion
tests — they are instructions for YOU (the LLM agent) to follow in a real
browser against a QA Luna with the plugin loaded.

Each scenario describes:
- What to do (chat turns to send, options to pick, cards to click)
- What to look for (rendered cards, meters, banner images, tool chips, worldd state)
- What counts as pass/fail

**E2E in this project means: you open a browser on a running Luna, play the
game, and judge the result with your own eyes (screenshots + DOM reading).**
You are the test runner and the assertion engine. No `expect()` calls.

Why: coded assertions only catch what you remembered to assert. An LLM reading
the full page catches broken cards, wrong meters, out-of-world prose, stale
options that should have been refused, and behavioral issues no matcher covers.

Engine math (combat, interest, regen, death) still gets ordinary unit tests —
per plan 001, both exist. The `StateBackend` contract tests must run against
**both** the local backend and the worldd HTTP client.

## 3. Execute the Plan

Implement phase by phase. After each phase:
- If worldd changed: restart the local `uvicorn app.main:app --port 8600 --reload`
  (or confirm reload picked it up) and hit `GET /health`.
- If the plugin changed: hot-reload it on the QA Luna (restart the Luna API if
  tool descriptions changed — tools only re-register on restart).
- If content YAML changed: run the content lint gate (schema validation,
  collisions, vocabulary lint) before committing.
- Check lints on edited files — fix any new errors.
- Commit the phase (submodule first, then parent pointer if applicable).

## 4. Run E2E Scenarios

Start the stack (see the **run-dojo** skill for preflight), then execute each
scenario from `tests/XXX-name/`:

1. Open the browser using MCP browser tools
2. Walk through each scenario file step by step
3. For every step: **screenshot + DOM snapshot** — read what's on screen
4. Judge pass/fail yourself based on what you observe
5. Fix anything broken. Re-run the scenario until you're satisfied.

**You are the test framework.**

## 5. Live Playthrough (MANDATORY — do not skip)

Coded tests passing is not enough. Before reporting the plan complete, follow
the **agent-live-walkthrough** skill: play the game through a real multi-turn
Luna conversation, observe the rendered cards and the agent's behavior, and
judge them qualitatively. Fix any regressions you find before reporting.

### 5a. The "first user query" check

Before opening the browser, write down — explicitly — the single most likely
thing the user will type to verify what you built. Then type that, exactly,
before reporting done. Examples:
- Shipped character creation? First query is `play linear ascent`, then trying
  to skip straight to the tower — the gate must refuse with a steering hint.
- Shipped the vault? First query is depositing, advancing a world day, and
  checking the interest actually posted (server-side, exactly once).
- Shipped a card type? First query is triggering it in chat AND replying with
  a plain-text number — the text fallback must always work.
- Shipped a worldd endpoint? First query is the same action from a **second
  tenant** — cross-tenant visibility is the whole point of the service.

The failure this prevents: the engine works in isolation, all tests pass, but
the integration with the real Luna chat (or the second tenant) was never
wired. The user's first turn exposes it instantly.

## 6. Report

Only after both E2E scenarios AND the live playthrough pass, report with:
- Summary of what was built
- E2E scenario results (per-scenario pass/fail with screenshot evidence)
- Live playthrough results + any fixes applied during it
- Any issues found and fixed
