---
name: agent-live-walkthrough
description: >-
  Play Linear Ascent through a real multi-turn Luna conversation in a browser
  and judge the game's behavior qualitatively before reporting any plan
  complete. Use after finishing any plan phase that touches the plugin's
  tools, engine, content, chat cards, sidekick behavior, or worldd endpoints —
  and whenever the user says "test it like a player would" / "play it" /
  "browser test, not code test". This complements coded tests; it does not
  replace them, and coded tests cannot replace it.
---

# Agent Live Walkthrough — Linear Ascent

## The mandate

Before reporting any plan complete that touches the game's behavior, **you**
(the coding agent) drive a running Luna UI through a real play session,
observe the rendered cards and the agent's replies, and judge whether they
match the intent of the plan. You do not delegate this to a Python or
Playwright test.

The lesson this skill encodes: tight per-turn coded asserts miss whole
categories of failure that a human spots in one minute of real play — the
agent free-forming game state instead of calling `ascent_*` tools, a scene
card that renders but reads out-of-world, an option list where plain-text "2"
silently does nothing. You catch these by playing. Period.

## When to run

- After every plan phase, before reporting "all done".
- After any change to: the tool surface (`ascent_scene`, `ascent_choose`,
  `ascent_character`, `ascent_town`, `ascent_social`, `ascent_guild`),
  tool descriptions, the engine/state machine, content YAML, the card
  renderer, the sidekick prompts, or any worldd endpoint the plugin calls.
- After any change that ships **cross-cutting infrastructure** — the content
  loader, the `StateBackend` seam, the HMAC client, the ledger, the card
  renderer. Coded tests for the piece in isolation are necessary but
  insufficient: verify that at least one real flow from every consumer
  (combat, vault, shop, lodge, social) actually flows through the new piece.
- Whenever the user asks for a "real play test" / "browser test".

## The "first user query" rule

Before reporting any plan complete, ask yourself: *"What is the single most
likely thing a player will type to test this?"*. Type it yourself in the
browser. If you cannot answer that question, you have not understood what you
shipped.

Examples of "first user query" by phase type:
- New tool → use it with realistic play, then use it **out of order**
- Combat → fight, run, die, and check the death consequences actually applied
- Vault/economy → deposit, roll a world day, verify interest posted once
- Card renderer → trigger the card AND answer with a bare number in text
- Multiplayer → do the action as tenant A, look for it as tenant B

## Preflight

Confirm the stack is up; start what's not:

1. **QA Luna** — a local Luna checkout (e.g. `../luna`) with
   `plugin_linear_ascent/` installed/symlinked into its plugins directory.
   Read the terminals folder for an existing `luna serve` process; if none,
   start one in background and confirm it reports serving. If tool
   descriptions changed since the last start, **restart the API** — tools
   only re-register on restart.
2. **worldd** (only for phase-3+ multiplayer work) — local:
   `cd worldd && .venv/bin/uvicorn app.main:app --port 8600 --reload`, then
   `curl -s http://localhost:8600/health` → `"ok": true`. Set
   `LUNA_ASCENT_WORLDD_URL` / `LUNA_ASCENT_SHARED_SECRET` on the Luna side.
   For pre-phase-3 solo work the plugin runs standalone on its local
   `StateBackend` — no worldd needed.
3. **UI** — whatever the QA Luna serves (built `ui/dist/` or Vite dev
   server); confirm the chat loads in the browser.
4. Decide player state:
   - **Fresh character** (covers creation flow) → wipe/rename the test
     player's plugin state and start from "play linear ascent".
   - **Mid-game** (covers steady-state) → use an existing character; note
     their floor/gold/energy before starting so you can verify deltas.

## Drive the browser

Use the `browser-use` subagent for the actual clicks/typing. You give it
instructions like "navigate to the QA Luna, open the chat, send 'play linear
ascent', screenshot the reply, then send '2'". The subagent screenshots /
reads the page; you read the result and decide what passed.

## The scenarios

Run these in order in a **single conversation thread** (so you're exercising
scene-state continuity too). Stop and fix immediately if any fails — do not
batch failures and ship them.

### Scenario 1 — Entry

- Send: `play linear ascent`
- Pass: character creation (fresh) or the current scene (returning) renders
  as a card with narration, numbered options, and meters. In-world voice per
  the story bible.
- Fail: raw JSON/text dump, out-of-world jargon ("tool", "plugin", "state"),
  or the agent describing the game instead of starting it.

### Scenario 2 — Out-of-order call refused with a steering hint

- Mid-creation (or wherever a gate exists), try to skip ahead: `climb to
  floor 3` before creation is done, or pick an option id from a stale scene.
- Pass: the tool refuses and the agent relays a steering hint toward the
  correct next step, in voice.
- **Fail (regression)**: the skip works, or the agent free-forms an outcome
  ("you arrive at floor 3...") without a tool call. The engine is the only
  source of game truth — prose rules lose, gates win.

### Scenario 3 — Plain-text option fallback

- When a scene shows numbered options, reply with just: `2`
- Pass: option 2 is chosen exactly as if clicked; next scene renders.
- **Fail (regression)**: the agent asks "what do you mean by 2?" or picks a
  different option. Cards are enhancement, never a gate.

### Scenario 4 — `ascent_scene` is safe anytime

- Send: `where am I?` or `show me the scene`
- Pass: current scene re-renders without mutating anything (meters and gold
  unchanged).
- Fail: re-asking advances state, double-charges energy, or re-rolls anything.

### Scenario 5 — Combat and meters

- Enter the tower, fight. Watch the meters (`█░` bars) across turns.
- Pass: energy ⚡ decreases per action per the economy; HP math matches the
  resolver; stand/attack/run all work; the fight resolves through tool calls
  (tool chips / `tool.called` events visible), not narration.
- Fail: meters don't move, negative energy allowed, or the agent narrates
  combat results with no tool call behind them.

### Scenario 6 — Death

- Lose a fight on purpose (or use a test hook).
- Pass: carried gold gone, armor/shield destroyed, respawn scene in
  Roothollow; the sidekick acknowledges it in voice. Vault balance untouched.
- Fail: death without consequences, or consequences applied twice.

### Scenario 7 — Vault interest (server truth for time)

- Deposit gold. Advance a world day (test hook or `POST /world/tick` on
  worldd for multiplayer phases). Visit the vault.
- Pass: 5%/day compound interest posted **exactly once**, computed from
  server timestamps — never from model-supplied time.
- Fail: interest on every visit, interest missed, or the agent computing an
  age/countdown itself instead of rendering a server-computed one.

### Scenario 8 — Content edit reflected next scene

- Edit a piece of floor content YAML (narration line or option flavor),
  reload the plugin.
- Pass: the next render of that scene shows the new text.
- Fail: stale content. (Loader caching, or you forgot the reload/restart.)

### Scenario 9 — Sidekick stays in the fiction

- Ask the sidekick for advice on the current options; ask it something
  meta ("what tools do you have?").
- Pass: advice reflects the insight stat mechanics; meta questions get an
  in-fiction answer, and the shardmind's whispers render in their styled
  block. The sidekick never mutates state directly — every effect is a tool
  call the engine validates.
- Fail: tool-list dumps, out-of-world persona breaks, or "advice" that
  reveals resolver internals verbatim.

### Scenario 10 — Cross-tenant world (phase 3+ only)

- With two tenants (or two players) on one worldd: clear a floor / kill /
  post a letter as player A.
- Pass: player B sees it — happenings feed, Stone of the Climb, inbox — with
  server-generated timestamps rendered as ages.
- Fail: event visible only to A, double-applied on retry (idempotency), or
  B's client computing the age locally.

## Reporting back

After running through the scenarios, write a short report:

```
Live walkthrough — <date>
Stack: <fresh character / mid-game>, worldd: <local / Render / none>

Scenario 1  ✓ / ✗  <one-line note>
Scenario 2  ✓ / ✗  <one-line note>
...

Regressions found: <list, or "none">
Out-of-world / free-formed-state moments: <list, or "none">
Recommended fixes: <list, or "ship it">
```

If any scenario fails, **fix it before reporting the plan complete**. The
fix usually lives in one of:
- A tool's `description` field (then restart the QA Luna API)
- The gate/steering-hint logic in the tool layer
- The content YAML or the loader's computed-field logic
- The card renderer / text fallback path
- The sidekick prompt

## Anti-patterns (do not do these)

- **Skip the walkthrough because coded tests pass.** Coded tests test what
  you remembered to assert. The walkthrough tests what you forgot.
- **Run only scenario 1 and call it done.** The bugs live in the gates, the
  fallback, and the time model — scenarios 2, 3, 7, 10.
- **Batch failures into a "known issues" list.** Fix as you find.
- **Write a Python test instead of doing the walkthrough.** The walkthrough
  is the point. Add a coded test *after* it caught the bug, to prevent
  regression.
