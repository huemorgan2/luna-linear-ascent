# Browser regressions

1. First walkthrough stopped on entering floor 1. Root cause: the actual engine emits a story Scene with `meters=None`; the inspector assumed every scene had meters, throwing a caught rendering error and leaving old controls disabled. Fixed the inspector to render that transition without inventing or retaining old meter values. Initial evidence preserved in `attempt-1/`. Full rerun required.

2. Narrow layout had 393px scroll width in a 390px viewport. Element boxes fit; text-range measurement traced the extra width to the 45-character engine entry-point identifier in `#source-summary` (right edge 393px, left 33px). Added wrapping to that provenance paragraph. Also retained fractional chart ticks for sub-five-day ranges so the Y axis does not repeat rounded 0/1 labels. Attempt-2/3 evidence is retained.

3. A rerun could briefly display the previous job's “Saved” status until the next poll; the walkthrough read that stale status before the new run ID existed. The submit handler now immediately shows Starting with an empty progress bar. The walkthrough also waits for a changed download ID, so it verifies the newly submitted result. Attempt-4 retained.

Final status: all three regressions resolved in the final full walkthrough (`browser-observations.json`, PASS, 21 recorded steps, zero JavaScript errors). Mobile document width equals the 390px viewport. Earlier failed attempts were not overwritten.
