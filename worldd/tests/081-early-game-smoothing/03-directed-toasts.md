# 03 — wires and letters pop in the live stream, sticky and clickable

## Preconditions
- Player A (sender, funded), player B (level-1 receiver), player C
  (bystander) — three separate browser contexts, all with the game pane
  open and feed toasts enabled.

## Scenario
1. A wires B ◈ 50. Start a stopwatch.
2. Watch B's screen: a toast should appear. Wait 30 s without touching
   it.
3. B clicks the toast body.
4. A sends B a letter. B waits for the letter toast, then clicks its ✕
   instead, and reloads the page.
5. Check C's screen and C's feed panel throughout.

## Expected behavior
- B's grant toast appears within ~4 s (one 2 s peek cycle + fetch),
  names the sender and amount, and is visually distinct (gold ink).
- It is STICKY: still on screen after 30 s idle (normal kill/climb
  toasts around it come and go in 3 s).
- Clicking it navigates to the Relay Office card with the grant letter
  waiting — even though B is level 1 (held post opens the door). The
  toast is gone after the click.
- The letter toast behaves the same; after ✕ + reload it does NOT come
  back.
- C never sees either toast, and neither row appears in C's world or
  faction feed panel.

## Fail conditions
- Toast auto-vanishing on the 3 s timer, or evicted by a burst of kill
  toasts.
- Click doing nothing, or landing anywhere but the Relay, or a red
  refusal (e.g. clicking while B is mid-fight must refuse politely, not
  break).
- The dismissed toast resurrecting after reload.
- ANY leakage to C — this is a privacy fail, file it as severe.
- Toast latency > 10 s.

## Verify
- `ascent_happenings`: the grant and letter rows have `scope='player'`
  and B's recipient columns; broadcast queries (`scope IN
  ('world','faction')`) do not return them.
- B's localStorage `la_ntf_seen` contains the dismissed/clicked ids.
- Two rapid grants in < 2 s both surface (the in-process feed cache does
  not swallow the second).
