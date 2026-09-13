# Power interruption recovery

13 September2026,10:42UTC. The user reported loss of power and authorized continuing. `/private/tmp/ascent-change-everything`, its QA launchers/credentials and uncopied phase4 browser evidence no longer exist. The root and plugin branch tips65bfdcf/56e1d86 match their remote branches. Committed code, phase3 browser evidence and the phase4 opening simulation survived. The original workspace's unrelated edits are unchanged.

Restored both `change_everything` worktrees under permanent `/Users/roy/Documents/my-projects-docs/ascent-change-everything` using the existing local objects. Obsolete missing worktree registrations are retained; no other worktree or branch was pruned. New private QA files/evidence will live under `/Users/roy/Documents/my-projects-docs/ascent-change-qa` with restricted permissions, not temporary storage.

## Database diagnosis and recovery steps

After reboot port5432 belongs to PostgreSQL16, whose database list has no candidate QA databases. PostgreSQL17's existing data directory `/opt/homebrew/var/postgresql@17` survives but its server is stopped. Do not replace or stop the running PostgreSQL16 instance.

1. Start the existing PostgreSQL17 cluster on free loopback port5433 using a command-line override, not a global configuration edit. Check the named QA databases and existing characters/ledgers/conversations. No database creation or restoration over existing data.
2. If the saved QA databases exist, make durable restricted local dumps before application restarts. Reuse recoverable tenant secrets privately. Recreate only lost local process settings/cookies; preserve all player and conversation rows. Report unavailable evidence or keys explicitly. Never infer a completed phase4 browser pass from a lost session.
3. Rebuild owned worldd8860/Luna8898 launchers to the durable source and5433 QA databases. Verify source/vendor, health, natural character balances, pending groups, one-time enrollment and tool registration before browser play. A new browser runner resumes the saved conversation; old subagent IDs are no longer available.
4. Continue phase4 pending exact arrow-query, effects, late-site and niche measurements, then phases5–8. All new run files/evidence stay in permanent directories; curate safe evidence into Git frequently.

## Rollback

Stop only newly recorded QA PIDs. If this operation starts PostgreSQL17, stop only that exact data directory using `pg_ctl -D /opt/homebrew/var/postgresql@17 stop -m fast`; leave PostgreSQL16 unchanged. Retain dumps, all databases, characters, receipts and durable worktrees. Do not delete earned state or overwrite it with an older snapshot. No production operation is authorized by this recovery.

Execution: PostgreSQL17 restarted successfully on5433; all four earlier QA databases survive. BaselineAsh45gold/25bank/2XP and naturalPhase3Luna8gold/13XP/act122/quiver-v1 recovered unchanged. Upgrade97 and one-time arrow enrollment98 persist. No database restored or player overwritten. Durable compressed dumps created before application restart (world211,943bytes,Luna173,777bytes). Existing tenant authentication recovered privately from its own QA row; lost local JWT/session key recreated. The QA vault has zero credentials, so recreating its lost local key loses no encrypted value. Owner username/password/conversation are unchanged; a new local session token targets the existing owner UUID.

Worldd8860/PID2949 and Luna8898/PID2950 restarted from durable launchers with the same databases and tenant, now on5433. Worldd health reports0.115.1/DBtrue; all150audited source/vendor files match. A replacement browser-use role resumes the preserved conversation and writes permanent evidence. Uncommitted earlier phase4 screenshots are unavailable after the power loss; earlier recorded failures remain failures and corrected rechecks need new evidence. A separate late-site world on8862/PID3871 was subsequently created under the committed MEASUREMENTS.md contract; the natural world's frontier remains3.
