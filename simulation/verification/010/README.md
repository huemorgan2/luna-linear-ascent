# Phase5 policy coverage experiments

First recorded run20260913T111536Z-bb54448d: unchanged engine0.115.2,12players×10days,seed32001,8availableCPUworkers,35.2342seconds, maxfloor30. Runtime decisions introduced real defensive honing, source-aware acquisition, owned weapon comparison, Vaultcollect/withdraw, route history and inexpensive road healing. No game coefficients changed.

Readyfloors by pair: Learner6/5, Tactician9/8, Planner10/10, Investor10/10, Experimenter8/8, Saver8/8. All players preserved; no refusal or decisionloop. Plannerfloor10times4.667/4.339days, Investor5.668/6.335. Thus the investor does NOT yet beat the planner in this sample. Actualinvestorinterest18/14gold,withdrawals855/734; records retain bank transfers rather than pretending deposits are expenses. Compared to earlier separate8player/seed31001run, more smartplayersarrive; this is not a paired causal estimate.

Initialstartercapability is alreadyfloor5 under this small4trialprobe; allsmartpairs showday0there. This is a preparedness measure, not proof of actual earlyaccess or completedwardenprogress. Strong-policyfloor10guide1.587days stillmissed. Currentprofile spends gold training and broad upgrades; further weapon/ammo/control and search work follows. All output retains exact engine/runner hashes and initialconfig.

An investor conservation test initially inspected the daily-present scene instead of the agent’s ordinary refreshed scene; reproducing the actual step restored the expected collect_interest option. Engineinterestwasalreadycorrect; no return coefficient was changed.

Parallel audit: parity-diagnostic.json records the pre-fix mismatch, caused by set-based navigation while sleeping. search/UNTRUSTED.md disqualifies the completed first search. After the explicit navigation/rest correction, all72tests pass20.999seconds (including serial/automaticCPU semantic hashes and replay). New search is stored separately.
