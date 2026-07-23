# worldd execution — Phase 3: Social — letters, grants, happenings, Stone, PvP

Parent: [plans/001-worldd](../../001-worldd/plan.md) phase 3.

## Goal

The LORD drama engine, cross-tenant: offline PvP, letters, grants, the daily gossip feed, and the Stone of the Climb.

## Deliverables

- `migrations/004_social.sql`: `pvp_attacks`, `letters` (with optional purse/item attachment), `grants`, `kills`, happenings kinds
- `app/pvp.py` — `GET /pvp/targets` (players "in the fields": not lodged, not beginner-protected L1–5, excluding self), `POST /pvp/attack` (2/day allotment, 3⚡, resolved server-side vs the defender's record: stats + luck rolls; winner takes carried gold + 5%-of-level XP bounty; kill row + happenings + optional taunt line)
- `app/social.py` — `POST /letters` (5g, purse/item attachment rules from economy §8), `GET /letters/inbox` (delivered on next session), `POST /grants` (10% burn, 150×level daily cap, receiver L5+ or guildmate), `GET /happenings/today`, `GET /stone` (frontier floor, first-clears, recent kills — server timestamps, client renders ages)
- Death-report events: a killed-offline player's next `/state` includes the full story (attacker, what was lost, taunt)
- Tests: allotment enforcement, beginner protection, grant caps/burn math, letter fees, idempotent attack resolution

## Exit gate

The 3-account drama scenario passes cross-tenant via API: A skips the lodge, B attacks and kills A (happenings row + kill on Stone), A's next state carries the death report, C sends A a grant and a letter; every gold movement reconciles in the ledger.
