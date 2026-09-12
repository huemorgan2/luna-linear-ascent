# S05 — Movement, effects, shields and arrivals

## Preconditions

Phases 3,4,7. Candidate push/bow/poison/stun weapons, full and broken shields, ground pursuer, fast flyer and immune creatures; known authored next arrival gap.

## Scenario

Push then fire a bow, push then escape, poison then switch, chain stun attempts, guard with strong Shield wall, and fight the next member without resetting resources. Repeat against an immunity and while exhausted. Land an ordinary bow hit against Power resistance and a spell/arcane-arrow hit against Magic resistance; inspect the rising pixel icons and damage numbers. Exercise Spell dispersal and mixed fire-arrow impact/burn. Repeat with reduced motion, mobile layout and a retried/re-rendered hit; inspect an existing player resistance where applicable.

## Expected behavior

Push opens an opportunity for the next normal combat action; flight closes distance faster; effects tick on their specified phases; shared resistance prevents permanent control. Landed hits leak HP, shield wear equals only absorption, and next arrivals obey their preview. Power resistance shows a rising pixel shield; Magic resistance shows a distinct rising pixel magic shield above the actual defender, alongside reduced HP damage. The log and static/reduced-motion version explain the same cause. Misses and exhaustion alone do not produce resistance feedback.

## Fail conditions

Zero HP loss from Shield wall, shield wear for a dodge, effects doubled by switching/exhaustion, free attack/heal/cooldown reset on kill, all arrivals silently at Cover, wrong-channel resistance icon, false full-block implication, popup above the next enemy, duplicate popup on retry, blurred/non-pixel art, or meaning lost without animation.

## Verify

Compare displayed damage/absorption/wear/gap and status durations to engine receipts. Pin small-number rounding and effect death-order examples in coded tests. Match each resistance popup/log entry to the authoritative event ID, defender, damage channel/cause and HP damage. Capture normal-motion and static/mobile feedback; the animation must not delay the next legal action.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
