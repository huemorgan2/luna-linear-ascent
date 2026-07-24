# Dojo 0004 — Interactive cards (clicks act, agent reacts) — 2026-07-24

Stack: QA Luna :8777 (fork, rebuilt UI), plugin 0.4.0, local backend
(solo), existing mid-game character (Torvald, human warrior, floor 1).

## What shipped

- **Luna fork (057)**: card-action postMessage bridge in `ChatPanel` —
  a card iframe posts `{type:"luna:card:action", nonce, path, body}`;
  the shell validates the source iframe, confines `path` to the posting
  plugin's `/api/p/<source>/` prefix, injects `conversation_id` +
  `message_id`, performs the authed fetch, and replies
  `luna:card:result` to that iframe only. `cardAction()` in `lib/api.ts`.
- **Plugin `/act` route**: pure engine loop — apply option, post next
  scene via `ctx.post_chat_card`, return. No model in the path.
- **Agent nudges**: `send_muted_message` fired only on big beats —
  `death`/`boss` → "moment" (agent reacts now, in voice),
  `present`/`letter`/`loot` → "awareness" (history only). Ordinary
  clicks: full silence.
- **Renderer**: options are real `<button class="opt">`s (chosen row
  violet, siblings 45 % + disabled, per chat_components.md), scene_id on
  `<body data-scene>`, 6 s no-bridge timeout reverts to
  "reply with a number" (stock-Luna safe).

## Scenario results

| # | Scenario | Result |
|---|---|---|
| 1 | Click an option button on the live card | ✓ chosen row lit violet, siblings dimmed/disabled, next card ~1–3 s, no agent bubble |
| 2 | 10-round combat grind by clicking | ✓ 1–7 s per round, meters exact (HP 42→39 on a 3-hit, ⚡ spent on hunt), wolf HP tracked |
| 3 | Death beat | ✓ red death-save card, muted "LINEAR ASCENT — DEATH" line, agent reacted in its own bubble, one line, in voice: "◆ You owe me." |
| 4 | Stale click on an old card | ✓ engine refused, posted current scene with steering hint ("That isn't one of the paths…") |
| 5 | Plain-text fallback: typed `2` | ✓ agent ran ascent_choose, healer's tent applied (HP 1→52, ◈−2). ~16 s vs ~2 s for clicks — the speedup is real |
| 6 | Reload persistence | ✓ 22 card rows reproduce; buttons re-enabled on history cards |
| 7 | Click on a refetched (post-reload) card | ✓ bridge works from persisted rows (`source` survives) — hunt → boar in 1.8 s |

## Unit coverage

- Plugin: 57/57 (`test_card_actions.py`: buttons, script wiring, shared
  runtime helpers, /act via TestClient, moment/awareness matrix).
- Luna UI: 9/9 (`057-card-action-bridge.test.tsx`: authed call + result
  reply, prefix confinement, foreign-window rejection, no-source cards
  inert; 056 suite still green).

## Findings / notes

- Regressions found: none.
- Latency grew to ~5–7 s on later grind rounds (page holds 20+ cards,
  each with typewriter + height observers). Fine for now; if it creeps,
  stop animating history cards (mock already prescribes "only the newest
  card types").
- The agent stayed silent through every ordinary click (correct per
  voice rules) and spoke exactly once, on the death moment.
- Old cards keep their pre-click enabled look after reload — acceptable:
  the engine refuses stale ids with a steering card (scenario 4).
