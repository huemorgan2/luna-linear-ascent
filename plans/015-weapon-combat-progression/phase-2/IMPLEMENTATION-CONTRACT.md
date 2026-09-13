# First implementation boundary

This specifies the first candidate schema before code changes. The complete group battle UI follows in phase3.

## Ownership

Each player stores `ruleset`, `collection`, `deck` (three nullable instance IDs), `active_weapon`, `item_sequence`, `materials`, `utility_tools`, `xp_reserve`, `group`, `expedition` and `collection_migration`. Each item stores ID, family, grade, upgrade level, current/max condition, acquisition source and provenance. Instance IDs derive deterministically from the owner key and a monotonic sequence. A selected ID appears once in the deck and must belong to that player; different IDs of the same family are legal. Tools never occupy a weapon cell.

Legacy weapons retain their exact slug, attack/hone investment, condition, oils and ownership location in a compatibility item until a fair explicit Forge conversion is offered. Mapping cannot throw away a paid high-tier weapon or silently give it a second honing multiplier. Read-only preview inventories held, packed and externally owned/pending assets separately; it never claims guild-held gear is personal property. Compatibility ownership is removed from slug containers only when the instance conversion is atomically recorded. A still-active old encounter delays conversion; it never grows extra opponents.

Fresh candidate players receive starter coverage through the opening. Existing players keep their collection and earned training; three available cells do not imply three free high-grade weapons. School slot compensation uses exact recorded `carry 2`/`carry 3` gold/XP receipts when present. Without receipts, a two-slot save gets30 gold/60XP and a three-slot save additionally200 gold/500XP: the original minimum fees, explicitly capped, never today's exponentially grown frontier fee. Refund once under a stable migration receipt; store XP beyond the bar in reserve.

## Persistence and requests

The world service must take a per-player transaction lock before loading or creating the document, inspecting a retry key or performing attendance side effects. Retry identity includes tenant, player and request ID. Compare supplied scene ID under that same lock. A stale action returns the current scene and a plain refusal without advancing the act counter or changing money, energy, RNG, item sequences or receipts. The local backend provides the same transaction boundary; runtime load/save separation is not sufficient.

Clients send the observed scene ID. Existing integrations may omit it during the compatibility interval, but a supplied value is never discarded. Retries reuse an operation's request ID. Web actions derive a stable retry key from player, observed scene and action payload when no explicit request ID is present. Two distinct actions against the same scene cannot both mutate it. A fresh scene is required before a second upgrade.

## XP and receipts

Available XP is current bar plus reserve. Earned XP fills the bar and preserves the rest; School spending and level purchase consume the same total without creating/destroying overflow. Level-up remains an explicit safe-town action, never a kill-triggered heal. At level30 the currency is uncapped. A settled kill cannot pay XP again, including after reload, retry or a failed final haul.

Group/member IDs, paid-or-exhausted latches, per-member rolled rewards and settled flags live with the active group. Expedition attempts and haul similarly persist. Closed groups use a monotonic sequence and compact settlement receipts; they cannot reopen from an old action. The durable host ledger keeps accounting history. Atomic deduct/create/settle operations produce one receipt with source identities.

## Verification and rollback

Test duplicate families and invalid duplicate IDs, three cells, legacy fight deferral, migration twice, source and condition preservation, School refunds once, overflow spending/level-up, scene wire round-trip, and local/HTTP stale/retry concurrency. Include two players using the same request ID. Reproduce the baseline double-deposit and show it executes once after the fix.

Candidate enrollment stays off in production. Before candidate writes, revert the implementation commits in reverse order. Afterwards, disable enrollment while retaining collection readers and safe settlement actions; use compensating receipts rather than restoring old player documents. Record applied commit IDs and exact tests in the phase execution status.
