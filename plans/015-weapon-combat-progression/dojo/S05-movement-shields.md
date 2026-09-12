# S05 — Movement, effects, shields and arrivals

## Preconditions

Phases 3,4,7. Candidate push/bow/poison/stun weapons, full and broken shields, ground pursuer, fast flyer and immune creatures; known authored next arrival gap.

## Scenario

Push then fire a bow, push then escape, poison then switch, chain stun attempts, guard with strong Shield wall, and fight the next member without resetting resources. Repeat against an immunity and while exhausted.

## Expected behavior

Push opens an opportunity for the next normal combat action; flight closes distance faster; effects tick on their specified phases; shared resistance prevents permanent control. Landed hits leak HP, shield wear equals only absorption, and next arrivals obey their preview.

## Fail conditions

Zero HP loss from Shield wall, shield wear for a dodge, effects doubled by switching/exhaustion, free attack/heal/cooldown reset on kill, or all arrivals silently at Cover.

## Verify

Compare displayed damage/absorption/wear/gap and status durations to engine receipts. Pin small-number rounding and effect death-order examples in coded tests.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
