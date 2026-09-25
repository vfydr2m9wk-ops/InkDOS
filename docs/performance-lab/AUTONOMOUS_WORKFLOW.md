# InkDOS autonomous performance workbench

Repository: vfydr2m9wk-ops/InkDOS

Branches:
- `main`: protected product branch. Never modify or merge from this process.
- `perf/xeros-optimization-lab`: hourly consolidated candidate only. Draft PR #203, DO NOT MERGE.
- `perf/xeros-optimization-workbench`: continuous experimental work. No merge authority.

## Authority model

Only the hourly review may decide KEEP, DROP, COMBINE, or RESET experiments.
Quarter-hour workers are producers, not judges. A worker must never stop later
workers because a local test is incomplete, inconclusive, unavailable, or failed.

A worker should continue to the next sufficiently separated READY task whenever
there is useful execution capacity. Local failure belongs to that task, not to the
whole chain.

## Worker cadence

Four hourly workers are offset by 15 minutes. Each uses a useful work window of
roughly half the interval when practical and may execute multiple READY tasks.
Prefer tasks in different lanes/files when stacking experiments in one hour.

For every task:
1. recover state and roadmap from /InkDOS Performance Lab;
2. inspect the exact relevant code/history/tests;
3. make the smallest implementation that tests the stated hypothesis;
4. preserve a dedicated commit/checkpoint;
5. run only a small directly relevant smoke/visual/timing check when feasible;
6. record COMPLETED, PARTIAL, or FAILED_TO_IMPLEMENT plus evidence;
7. continue to another READY task when practical.

Do not revert merely because a quick benchmark is neutral or a test is incomplete.
Do revert immediately only when the implementation itself cannot safely remain on
the workbench (syntax corruption, unusable app, destructive data behavior, or clear
security bypass). Record such a local emergency revert and continue other tasks.

## Hourly review

The hourly review is the sole decision authority. It:
- reads every experiment/checkpoint since hour_base_sha;
- inspects available focused evidence;
- evaluates independence/interactions;
- selects a coherent subset;
- reviews the sequential workbench task commits from the hour and removes only rejected bounded changes;
- writes the exact reviewed workbench SHA to state.reviewed_workbench_sha and state.stage_ready_sha;
- leaves the lab branch untouched during review;
- lets the :05 Stage worker move perf/xeros-optimization-lab to exactly stage_ready_sha;
- uses draft PR #203 as the complete CI gate for that staged SHA;
- on the next review, inspects numeric, visual, behavioral, security, offline and launchQueue evidence for the staged candidate;
- updates stable_sha, roadmap priorities and dead hypotheses while keeping unrelated work moving.

Do not merge PR #203 or main. Do not enable auto-merge. No releases/tags/version
bumps/deployments.

## Evidence hierarchy

Real XeOS/iPad observations are the perceptual target:
- Presentations: about 5 seconds average open time reported on XeOS.
- PDF: about 20 seconds for an approximately 16,000-page PDF.

CI is comparative evidence, not a substitute for those device measurements.

## Persistent state

Personal Library folder: `/InkDOS Performance Lab`
- roadmap.json
- state.json
- performance-experiments.jsonl
- worker-log.txt
- latest-hourly-review.txt
- hourly-review-NN.txt

Workers append experiments; hourly review owns roadmap/stable decisions. Stage worker owns only mechanical staging of the review-approved SHA and has no KEEP/DROP authority.
