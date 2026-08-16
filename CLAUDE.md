# luna-service — workspace rules

## devprocess (mandatory for all changes)

**Every code change follows devprocess — plan-driven execution.**

### Principles
- **Track before fix.** Reproduce and root-cause before touching anything; never point-fix a symptom.
- **Act, don't delegate.** If the agent can do it, it does it and reports the result.
- **Everything reversible has a rollback written before execution.** Everything irreversible gets confirmed first.
- **Report faithfully.** Numbers, not adjectives. Failures are stated plainly.

### Plans
Plans live at `plans/NNN-short-slug/PLAN.md`.

PLAN.md contains: Problem (with evidence and timeline), Root cause, emergency mitigation already taken, Fix split into phases, Verification, and Operational notes.

Multi-phase work gets one sub-folder per phase — `phase-1/PLAN.md`, `phase-2/PLAN.md` — each with:
- **Goal** — one paragraph, measurable.
- **Steps** — concrete commands/edits, including who inherits the change.
- **Verification** — exact queries/requests that prove the phase worked.
- **Rollback** — exact inverse operation.

Plans are committed before execution starts.

### Execution
- Execute phases in order; each phase is verified before the next begins.
- Snapshot before fleet ops.
- Canary first. One instance, health-checked, then the fleet.
- Changes must land in **both places**: live system AND code path that provisions new ones.
- Temporary access is opened narrowly and reverted immediately after use.
- Secrets never enter a repo. Secret-pattern scan before every commit.

### Testing and deploy
- Targeted tests for the change, then the full suite.
- Deploy is explicit: push, trigger deploy via API, poll to live.
- Post-deploy verification is part of the deploy.
- After execution, append "Execution status" to each phase PLAN.md. Commit.

---

## dojo tests (mandatory for verification)

**Dojo tests are end-to-end scenarios executed by an LLM agent in a real browser (Playwright). They complement coded tests and CI — they never replace them.**

### What they are
A dojo test is a markdown scenario that an agent walks step by step in a real browser, taking screenshots, inspecting DB and logs, and judging pass/fail with evidence — the way a careful human tester would. The same scenarios run again and again to verify the system still behaves.

### Why
Coded tests assert what you predicted. Dojo tests judge what actually happened. They catch what assertions miss:
- A flow that "works" but redirects to the wrong URL
- A tenant that boots with another user's credentials (returns 200 everywhere)
- A provisioning flow that passes but takes 90 seconds with no progress indicator
- A "ready" page that appears before the thing is actually ready

### Anatomy of a scenario (one .md file, five sections)
1. **Preconditions** — state that must exist before starting
2. **Scenario** — step-by-step actions: open browser, click, type, wait
3. **Expected behavior** — described in human terms, not regex
4. **Fail conditions** — specific anti-patterns that indicate a regression
5. **Verify** — what to check in DB, logs, or UI beyond the surface

### Key properties
- **Multi-user is first-class.** The interesting test is "A signs up, B signs up, A logs back in — is A's data intact?"
- **Time matters.** Scenarios assert "completes within X seconds," not just "completes."
- **State spans systems.** Verification crosses DB, storage, env vars — not just UI.
- **Failure modes are exercised.** Provider down, machine fails, partial provisioning.

### Results
Every run writes a numbered results folder: summary.md (date, commit SHAs, environment), per-scenario PASS/FAIL table with notes, screenshots, and regressions list. Regressions are filed, not quietly fixed mid-run.

### Rules
- The LLM is the test runner and the judge; evidence backs every verdict.
- Scenarios mirror implementation phases — every plan ships with its dojo scenarios.
- **A dojo walkthrough is mandatory before a plan is reported complete.**
- Local runs use the same code paths as production.
- Tests live in `luna/dojo/tests/` and run with: `TOKEN=<jwt> BASE=<url> node tests/<name>/walkthrough.mjs`
