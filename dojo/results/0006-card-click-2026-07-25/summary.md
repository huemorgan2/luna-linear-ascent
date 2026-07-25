# Dojo run 0006 — card option clicks (2026-07-25)

## Complaint

Clicking a game option in the chat card did nothing; the player still had to
type the number. The card's own script showed `…` then reverted after its
6-second timeout — because no host was listening.

## Root cause

The 057 card-action bridge (`luna:card:action` postMessage listener +
`cardAction` API in ChatPanel) lived only on the Luna fork branch
`056-followup-card-ordering` (commit `c855ff3`). It was never merged to
`main`. Production machines were upgraded to 0.48.005/6 (built from `main`),
silently dropping the bridge that had been verified live on the 0.47.004+
branch build.

## Fix

Cherry-picked onto `main` (branch `059-card-action-bridge`, merged as
`958b9da`, version **0.48.007**):

- `c855ff3` — 057 card-action bridge + card follow-scroll + height cap 1400
- `9a2b80c` — 056 followup: `message.created` carries `created_at`, UI
  inserts live cards in timeline order

Tests: UI 115/115 (incl. `057-card-action-bridge.test.tsx`), `tsc -b` clean.

## Verification

QA Luna (localhost:8777, rebuilt ui/dist):

- click "Floor 1" on the gate card → "Lamplit Steading" card in **0.6s**
- click "Hunt the wilds" on the new card → wolf fight card in **0.6s**

Production (luna.com.ai, after deploy):

- click "Hunt the wilds again" in Cortana's chat → "Feral boar" fight card
  in **2.7s**, chosen button highlighted, no typing
  (`screenshots/prod-02-after.png`)

## Deploy

Plan-033 pipeline driven through the admin session (Playwright MCP was
disconnected; reused its Chrome profile copy at /tmp/deploy-chrome-profile):

- build `0.48.007` from `main@958b9da` → built in ~2.5 min
- promote-main: migrated **30/30 machines, zero errors**
- vaselin-gamer's Fly machine stayed `stopped` after migration (502 on
  first load) — explicit `POST /api/agents/<id>/start` + cold boot fixed it

## Side effect

The production verification click legitimately played a turn: spent 1⚡ and
started a feral boar fight in the owner's game.
