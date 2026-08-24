# Scenario: portrait gear placement (figure3d harness)

## Preconditions

- Local worldd running: `uvicorn app.main:app --port 8600` from `worldd/`,
  `GET /health` returns ok.
- Browser opens `http://127.0.0.1:8600/static/site/figure3d/test.html?fig3ddebug=1`
  (fresh cache-busting query each reload).

## Scenario

1. Open the harness; wait ~6s for all three stages to mount and settle into
   idle.
2. For each race (human, elf, giant): enlarge that figure's canvas to ~4×
   (set CSS height via console) and screenshot the full figure, plus one
   close crop of the weapon hand / hip region.
3. Hover each gear-map slot once and confirm the matching piece tints.

## Expected behavior

- **Human**: round buckler hanging OUTSIDE the line of his left forearm
  (screen right), not overlapping the torso and not tucked inside the arm;
  sword on the opposite hip, hanging near-vertical, hilt at palm height,
  readable against the leg.
- **Elf**: bow slung diagonally across the back, limbs visible above the
  shoulder and beside the hip; her sword placed like the human's; shield
  outside the forearm.
- **Giant**: staff STANDING — vertical, shaft passing through his right
  fist volume, clearly in front of / beside his body silhouette (not lying
  on the torso, not clipped by the frame edge); shield outside his left arm.
- All gear survives the 1-bit tone curve (visible against black at a glance,
  no pixel-hunting).

## Fail conditions

- Any weapon intersecting the torso silhouette so it reads as "passing
  through the body".
- Shield rendering as a cylinder/edge sliver, or inside the arm line.
- A listed item invisible at a glance (tone-crushed or occluded).
- Staff floating detached from the hand, or lying diagonal on the body.
- Hover tint applied to the wrong piece, or stuck after unhover.

## Verify

- Console: `window.fig3dLives` world-bbox dump per slot — every prop bbox
  inside its frame (giant frame x ∈ [-0.59, 0.59]) and overlapping the
  expected body region (e.g. staff x-range beside body, not centred on it).
- No WebGL errors in the console; fallback `<img>` still hidden.
