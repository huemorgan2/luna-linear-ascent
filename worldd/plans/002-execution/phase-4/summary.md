# worldd Phase 4 — execution summary (bosses, guilds, frontier)

Status: **complete** (two-player quorum tested cross-tenant).

## Built

- Boss quorum commits: milestone keeps route to the pledge flow (5⚡ escrow, `ascent_boss_commits`, pledges valid 2 world-days). The commit that completes the quorum resolves the fight **immediately in the same transaction** — no cron: party power vs boss power with a deterministic ±10% swing, full milestone XP/gold per committer on victory, energy refund on defeat, result cards queued to every committer's `pending_events`.
- Frontier: victory raises `ascent_world['frontier']` (floor+1) for every tenant; happenings + Stone inscription written.
- Guilds: found (◈500, name via chat), join/leave, roster from live player docs; guild stored in the player doc + `ascent_guilds` registry.

## Deviations

- Guild board and watchtower deferred (001 open decision) — noted for phase 7 polish.
- Quorum counts use economy.MILESTONES as configured (Gnarl 2 for small launch).

## Verified

`test_gnarl_quorum_two_players`: two players, two tenants, pledges on separate turns; resolution fires once on the second pledge; both get "Gnarl has fallen" cards with rewards; frontier ≥ 11 for the whole world; names carved on the Stone. Engine-side: keep routing, pledge cost, quorum dots (`test_milestone_keep_routes_to_quorum_with_world`).
