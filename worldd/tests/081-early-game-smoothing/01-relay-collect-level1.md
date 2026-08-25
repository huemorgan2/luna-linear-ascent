# 01 — level-1 player collects wired gold on the first click

## Preconditions
- Player A: level ≥ 2, gold ≥ 200.
- Player B: fresh level-1 climber, never received a letter, gold noted
  as G0.
- Both logged in, separate browser contexts.

## Scenario
1. A opens B's profile and sends ◈ 100 (`pf_pay`), or uses the Vault
   grants desk.
2. B opens the game pane. Note whether the Relay is reachable (a COLLECT
   notice or an open Relay door must appear — level 1 has no door of its
   own, held post opens it).
3. B enters the Relay Office. Screenshot the card: the letter with
   "[◈ N enclosed]" and the *Collect the enclosed gold* row.
4. B clicks *Collect* ONCE. Screenshot the returned card immediately.
5. B clicks wherever the Collect row was (or re-opens the Relay) —
   deliberately poking at stale UI.

## Expected behavior
- Step 4's card already shows: gold meter = G0 + net, NO Collect row,
  NO "[◈ enclosed]" line, the clerk's counting note, and the COLLECT
  notice gone. Within ~10 s total from step 1.
- Step 5 produces either a calm clerk line ("nothing more for you") or a
  normal Relay/locked-door card — nothing alarming.

## Fail conditions
- Any red top banner, especially "That isn't one of the paths".
- The post-collect card still showing the Collect row or the
  pre-collect gold figure (the one-turn-stale card regression).
- B's gold not incremented, or incremented twice.
- The Relay looking "🔒 level 2" in a way that implies the money is gone
  while the ledger says it was paid.

## Verify
- `ascent_ledger` for B: exactly one `kind='letter_gold'` row and one
  `grant_in`, amounts matching; A has one `grant_out`.
- `ascent_letters` for B: the grant letter `read = TRUE`, `gold = 0`.
- B's doc gold == G0 + net.
- Server logs: zero unknown-option refusals for B during the run.
