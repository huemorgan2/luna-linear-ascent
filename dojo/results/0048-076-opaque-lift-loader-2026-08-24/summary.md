# Dojo run 0048 — 076 opaque lift loader

- **Date:** 2026-08-24
- **Environment:** local worldd on `:8600`, authenticated `/play`
- **Scenario:** `tests/076-lift-transitions/01-opaque-loader-stage.md`
- **Verdict:** PASS

## Results

- **Ascent:** PASS. `#liftlay > .car > .ink`; `.car` computed background
  `rgb(0, 0, 0)`, 640x224; `.ink` used
  `lift_ascent_320x112.gif?t=<nonce>`.
- **Descent:** PASS. Same opaque stage; `.ink` used
  `lift_descent_320x112.gif?t=<nonce>`.
- **Destination underlay:** PASS. Destination `data-loc` was present while
  `#liftlay` existed (`gate_town` during ascent, `town` during descent).
- **Fade and usability:** PASS. Overlay was removed in about 5.6 seconds and
  each destination was immediately interactive.
- **Errors:** zero console errors and zero failed network requests.

## Coded verification

- Plugin 076 target: `11 passed`.
- worldd 076 target: `2 passed`.
- Full plugin suite: `1356 passed, 1 skipped, 1 xfailed, 4 failed`.
  The four failures are the unrelated class/kill3d regressions already
  recorded by dojo run 0047.

## Deployment

Not performed.
