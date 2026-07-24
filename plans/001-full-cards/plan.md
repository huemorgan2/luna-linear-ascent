# 001 — Full cards: the game speaks for itself, the sidekick shuts up

Status: PLANNED
Scope: coordination plan across the three repos in this workspace.
Companion docs:
- **Luna core proposal:** `luna/plans/056-standalone-plugin-cards/plan-suggestion.md`
  (standalone `kind:"card"` messages, embed auto-height, `ctx.post_chat_card`,
  empty-reply suppression — the host capabilities this plan consumes)
- **Plugin execution detail:** `plugin-linear-ascent/plans/003-execution/phase-9/plan.md`

## The problem (as reported playing the game)

1. Scene cards render inside the agent's message bubble with a 500px
   max-height iframe → inner scrollbar, cramped, feels like a quote.
2. The game appears to be *authored by the agent*. A scene should be a step
   in the chat — the world acts, then the player and the agent both react
   to it. If a dragon appears, the dragon appears; the agent is thinking
   and *might* respond — or might not.
3. The agent narrates the obvious ("a dragon! we can attack, stray, or
   run") — it re-reads the card to the player. That ruins pacing and buries
   the game under text.

## Target behavior

- **Scene = its own timeline block.** Full width, no avatar, no bubble, no
  inner scroll. Persisted; reload reproduces the timeline.
- **Agent = sidekick, not narrator.** After a scene: at most ONE short
  in-character sentence, and only when it adds signal the card can't show —
  a tactical read ("It's wounded and we hit hard — one strike ends it"),
  a warning, a synergy. Otherwise: silence, and silence leaves no empty
  bubble.
- **Nothing already shipped breaks.** Phase-8 (vault join flow, settings
  tab, worldd enroll, marketplace 0.2.0) untouched; stock-Luna installs
  keep working via fallback.

## Workstreams and where they live

### W1 — Luna fork (submodule `luna`) — implement plan 056

Four additive changes, detailed in the 056 suggestion doc:
1. `kind:"card"` message shape + promotion + bubble-less full-width render.
2. Embed auto-height via `luna:embed:height` postMessage (source-checked,
   capped ~900px; old 500px cap stays as fallback). Fixes the scrollbar for
   ALL plugin embeds, not just cards.
3. `ctx.post_chat_card(html) -> message_id | None` on the SDK.
4. Suppress empty assistant bubbles (silence support).

Plus: card rows are excluded from model history (scene context reaches the
model exactly once, via the tool result).

### W2 — Plugin 0.3.0 (submodule `plugin-linear-ascent`) — phase 9

1. Tools feature-detect `ctx.post_chat_card`:
   - present → post the rendered card as a standalone message; return to
     the model only `{scene_text, instructions}`;
   - absent (stock Luna) → return today's `{scene_text, embed_iframe,
     instructions}` — exact 0.2.0 behavior, zero regression.
2. `render.py` cards gain the height-reporting script (harmless on old
   hosts).
3. Version 0.3.0 in `version.py` + `luna-plugin.toml`.
4. No worldd changes; no tool-schema changes.

### W3 — Sidekick voice (plugin instructions; biggest UX win)

Calibration (revised 2026-07-24: the sin is *redundancy*, not speech — the
sidekick is a character, don't mute it). Rewrite `_SHARED_RULES`/
`_EMBED_RULES` and tool descriptions:
- HARD RULE: never repeat, summarize, or re-list anything visible on the
  card — no re-describing the scene, no reading out the options;
- at most ONE short in-character sentence (two only for boss/death-level
  moments);
- a short line is usually welcome, of one of two kinds:
  - a tactical read when there's real signal ("Wounded and slow — one
    strike ends it", "We can't take two hits at 4 HP — lodge first");
  - a flavor/personality beat when there isn't ("That smell again.
    Wardens.");
- go silent (empty reply) during repetitive beats — mid-combat grind,
  the third fight in a row, routine shop visits — where any comment is
  noise;
- always speak on notable beats: new floor, boss, near-death, level-up,
  rare loot;
- include ~4 contrastive calibration examples (good tactical line / good
  flavor line / good silence / bad narration) — examples steer models
  better than adjectives.

## Execution order

1. W1 items 1–2 in the Luna fork → rebuild the UI → restart QA Luna (8777).
2. W1 items 3–4, then W2 → browser check: cards standalone + scroll-free;
   temporarily hide `post_chat_card` to prove the stock-Luna fallback.
3. W3 → dojo-style multi-turn playtest (real browser, real conversation):
   creation → town → 3 fights → a warden/boss encounter. Assert:
   - every agent bubble ≤ 1 short sentence (≤ 2 on boss/death beats);
   - ≥ 1 repetitive scene gets pure silence; big beats always get a line;
   - no bubble re-lists card options or re-describes the scene;
   - cards survive page reload;
   - phase-8 regression: settings tab join/disconnect still works after the
     Luna rebuild.
4. Tests: plugin suite (payload fork both branches); Luna-side unit tests
   per the 056 doc.
5. Ship: commit Luna fork (PR-able series, upstream candidate), publish
   plugin 0.3.0 to the marketplace, write
   `plugin-linear-ascent/plans/003-execution/phase-9/summary.md`.

## Risks

- **Stock-Luna marketplace users** see the fallback (in-bubble cards) until
  056 lands upstream. Acceptable; note in the plugin README.
- **Model silence compliance** varies; if a model can't emit an empty
  reply, instruct a bare "◆" and add it to the suppression list.
- **Background/scheduled tool runs** must not post cards into the wrong
  conversation: `post_chat_card` resolves from the run context or returns
  `None` (→ inline fallback).
- **Double scene context** in history — guarded by the history-exclusion
  rule in W1.
