# Mining dojo scenarios — proposed, not run

These scenarios belong to the separate [mining project](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plans/013-mining-and-gathering/PLAN.md). Each future run must create a numbered results folder with environment and commit SHAs, screenshots, PASS/FAIL evidence, and a regressions list. No scenario below is marked passed by this research.

## Phase 1: eligibility, energy, and an unbanked haul

**Preconditions:** A QA player has reached floor 3, has a known energy balance, owns one correct tool, and has known quantities of pre-existing materials. Mining implementation and tools are enabled in QA.

**Scenario:** In a real Luna conversation and browser, inspect the forest and metal sites. Try the wrong tool, then use the correct tool. Make three collection attempts. Refresh and reopen the site. Extract once, then retry the same extraction request through the normal client retry fixture.

**Expected behavior:** The card explains the tool restriction before spending energy. Each accepted attempt spends exactly one energy and shows the resulting haul. Refresh preserves the haul. Extraction moves the haul to the Materials compartment once.

**Fail conditions:** An invalid attempt spends energy; a refresh rerolls; materials vanish because the ordinary pack is full; extraction duplicates units; the UI shows a banked balance while the haul is still at risk.

**Verify:** Compare player document, energy timestamps, material balances, haul, and ledger. Require visible feedback within two seconds on the QA connection, or record measured delay as a failure needing investigation.

## Phase 2: encounter victory and continuing a trip

**Preconditions:** The QA seed reliably produces a site encounter, and the player can win with the correct counter. Record a nonzero haul.

**Scenario:** Gather until the encounter appears; inspect its type; fight it through browser actions; win; continue one gathering attempt; extract.

**Expected behavior:** Gathering pauses during combat. The enemy belongs to the site's theme. Victory adds a stated quantity of the targeted material to the unbanked haul. The player can continue or extract.

**Fail conditions:** Victory rewards an unrelated material, rolls twice, auto-banks the whole haul, bypasses combat costs, or returns to town while leaving the expedition inaccessible.

**Verify:** Inspect combat and material receipts, encounter state, one-time reward identifier, and before/after material quantities.

## Phase 2: death loses this expedition only

**Preconditions:** Record pre-existing stored materials and a nonzero expedition haul. Use a QA state with death protections explicitly known and a site enemy capable of killing the player.

**Scenario:** Fight and die through the real browser. Return to the pack, reopen the site, and reconnect once. Repeat separately for an active death-prevention effect to verify its documented outcome.

**Expected behavior:** Actual death removes all current-trip material and leaves earlier stored material intact. The receipt states the loss. Reconnecting cannot recover the lost trip or apply the penalty twice.

**Fail conditions:** Pre-trip resources disappear, any expedition loot survives actual death contrary to the rule, or a save/escape uses an undefined result.

**Verify:** Check the death outcome, material compartment, expedition state, and loss ledger. Compare exact counts to the preconditions.

## Phase 3: high-floor gates and independent players

**Preconditions:** Player A has early-floor access; player B has reached floor 80. Use separate browser sessions and known balances.

**Scenario:** A inspects the Legendary material source hints and attempts site access. B visits both high-floor sites, gathers, and extracts. Switch back to A and inspect the pack and available sites.

**Expected behavior:** A cannot mine Legendary material through a direct link or B's open card. B can use the sites with correct tools. A's inventory and progression are unchanged.

**Fail conditions:** World visibility substitutes for required personal eligibility, a card affects the other player, or the wrong player's tool/energy is used.

**Verify:** Compare both documents and request identities, inspect access refusal logs, and capture screenshots from both accounts.

## Phase 3: gather, upgrade, and compare routes

**Preconditions:** A QA player has a weapon one recipe short of its next level and enough gold. Two distinct gathering routes have documented odds, tool costs, and enemy profiles.

**Scenario:** Gather the missing material, extract, inspect the weapon's progress, follow “Upgrade in the Forge,” and upgrade. In separate seeded QA sessions, compare a suitable route/tool/counter with an unsuitable choice over a predetermined energy budget.

**Expected behavior:** The material balance refreshes on the card; the Forge consumes the exact inputs once. Better choices provide the predicted opportunity to progress faster; the two routes are not secretly normalized to equal rewards.

**Fail conditions:** An unextracted haul can pay for the weapon, the upgrade executes outside the Forge, or the route comparison is decided from a single lucky roll.

**Verify:** Check exact upgrade and extraction transactions. Use repeated coded simulations for reward distributions and real browser play to judge clarity and decisions. Neither substitutes for the other.
