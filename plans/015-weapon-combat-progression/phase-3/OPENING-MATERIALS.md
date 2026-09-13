# Opening material correction — before execution

## Evidence and root cause

On13 September, natural Phase3Luna cleared six floor1 groups and reached243gold/23XP with no materials, then faced171gold+2Wood+6RawMetal for the starter blade's first upgrade and80gold for both gathering tools. The30-day simulator takes13–20days for careful players to reach floor10, versus the1.5875day strong-policy target. These observations do not alone prove a balance defect, but source comparison found a definite contract discrepancy: `bestiary.roll_rewards` selects only one material and awards one unit on early floors. The approved research and published wiki specify both materials in a4Y-unit bundle, with3:1/1:3/2:2 carrier composition and Y capped5. Current catalog still labels these as material bundles. No recorded phase3 decision explains the reduction.

## Correction

Restore both materials on each successful grade roll, using Y=min(5,1+max(0,floor−grade_start)//6). Keep every grade probability, specimen/deep multiplier and categorical weapon roll unchanged. Carrier identity follows the candidate's intended weapon reward route: Air favors A/bows, Ground Magic favors B/blades, other Ground mixed. Document this candidate distinction when phase4 regenerates the wiki; do not reuse the older Power-ground carrier assignment silently.

Make bundle quantities an engine-owned public record in each persisted member. Existing rolled rewards are never re-rolled or enlarged on reload. New members record bundle composition and reward revision; saved older groups without it render odds without inventing quantities. Apply the same rule to actual site ambushes rescaled to site floor.

The two opening gathering sites currently yield only one target unit at58%/47%. Set each successful collection to two target units, keeping unequal success/ambush probabilities, tool prices/wear and bonus-per-defeated-ambusher unchanged. This is an explicit candidate tuning experiment to keep targeted gathering useful after restoring monster bundles; compare secured materials per energy and full recipe time in the same real engine. It is not an accepted1.5–2.5× return claim until measured. Tools remain outside the deck. Previously collected haul is unchanged.

## Verification

Focused exact tests: every carrier awards both quantities at floor/grade boundaries; early high-grade discovery stillY1; maxY5; independent material grades; unchanged categorical one-weapon limit; old pending rewards retained; gather costs exactlyone energy and yields two secured units only on extraction, with retry retaining balances. Follow with full plugin suite and simulator suite, source-pinned matched10/30-day runs and exact replay. Record actual progression and any remaining bottleneck rather than overwrite earlier runs. Revisit actual natural player's earned path with no grants, plus the existing gathering fixture; keep all earlier evidence.

## Rollback

Revert the recorded bundle/yield commit, vendor and restart only ownedQA processes. Keep all previously earned materials, old/new pending reward snapshots and receipts. Newly introduced optional public fields must remain readable by old clients. Disabling the candidate enrollment flag does not convert existing players or undo earned progress. No production operation.

## Candidate checkpoint

Plugin c062bee/0.114.4 restored bundles/two-unitnewexpeditions and narrow CSS.69focused tests passed; full1511passed/8knownlegacyfailures/4skips/1xfail in90.92s; simulator62passed54.00s; HTTP8passed7.75s. The following guidance-only e029396/0.114.5 changes scene metadata, not economic outcomes;70focused and6candidateCPU/replaychecks passed, full1512passed/8samelegacyfailures/4skips/1xfail102.78s. Service-wide followup is running.

Measurements are in simulation/verification/007. Three of8 now reach10within10days (previouslyzero); the fast repeated-policy target stillmissed.64preparedroute trials each show Wood2.666× and RawMetal1.787× securedtargetunits perpaidenergy versus hunting, includingambushenergy. Those units cost the sites' ordinarytoolprice and give muchlessgold; no forcedequalreturn. Oldpendingrewards andoldactiveexpeditionone-unitrules are separately tested, never enlarged on reread. Currentnatural browserplayer remainsungifted and willrechecknewexpedition/Forge.

Exact reversal before restartingcandidateQA: revert e029396 then c062bee inplugin, vendor/restartownedQA. AftercurrentnewQA writes, retainreaders andold/newexpedition snapshots; prior earnedmaterialamounts remainvalid. Never restorepre-experimentplayerdocuments overearnedstate.
