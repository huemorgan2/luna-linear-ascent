# worldd Phase 3 — execution summary (social)

Status: **complete** (cross-tenant integration-tested).

## Pattern

The sync engine stays pure: worldd **injects** `doc["_world"]` (inbox, names, PvP targets, grant targets, guilds, boss commits, happenings, stone, frontier) before each turn, and **executes** `doc["_effects"]` (cross-player writes) after — one transaction, so a turn fully lands or fully rolls back. Offline delivery via `pending_events` in the recipient's doc, popped on their next scene.

## Built

- Schema (`003_social.sql`): letters (with enclosed gold), happenings, boss commits, guilds, stone lines.
- Letters: Relay Office scenes, 5g send, free-text body via chat, enclosed-gold collection; read-marking via `letters_seen` effect.
- Grants: Vault grants desk — 10% burn, 150×level daily cap, L5+ receivers, delivered as gold-bearing letters; vanished-receiver refund.
- PvP: fields target list (unlodged, above L5 beginner protection, not self), 2/day + 3⚡ costs enforced by the engine, deterministic power+swing resolution, carried-gold transfer, XP bounty, victim death-report card queued, attacker outcome card queued, happenings line, ledger rows both sides.
- Happenings & Stone: town square shows the last day's news; the Stone shows frontier + boss inscriptions.

## Verified (worldd tests + engine tests)

`test_full_drama_loop`: A ambushes unlodged B across tenants → attacker outcome card → B's next session opens with the death report → the square carries the news. `test_letter_and_grant_flow`: letter body delivered verbatim; 100 granted arrives as 90 (burn) and collects at the relay. Engine-side: costs, caps, and effect emission (8 social unit tests).
