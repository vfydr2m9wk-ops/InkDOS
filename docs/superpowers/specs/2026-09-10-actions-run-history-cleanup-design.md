# GitHub Actions Legacy Run Cleanup Design

Date: 2026-09-10
Status: approved intent, pending implementation
Depends on: `docs/superpowers/specs/2026-09-10-actions-workflow-consolidation-design.md`

## Goal

Delete obsolete GitHub Actions run history created by superseded workflows after workflow consolidation, while preserving the five permanent workflows, current/future runs from those workflows, the cleanup run itself, and run IDs that are explicit freeze/refreeze evidence.

## Scope

This is repository-maintenance only. It does not delete commits, branches, releases, artifacts outside the deleted runs, application files, tests, or the five permanent workflow definitions.

The cleanup is one-shot. No permanent scheduled history-pruning workflow is introduced.

## Preconditions

The cleanup may execute only after the consolidated workflow set is present on `main` and the legacy workflow YAML files are absent from `main`.

The permanent workflow paths are:

- `.github/workflows/workspace-regression.yml`
- `.github/workflows/integration-regression.yml`
- `.github/workflows/stability-freeze.yml`
- `.github/workflows/apply-inkdos-update.yml`
- `.github/workflows/refresh-integrity-metadata.yml`

## Preservation rules

A workflow run must be preserved when any of these conditions is true:

1. Its workflow ID belongs to one of the five permanent workflow paths above.
2. Its run ID is the currently executing cleanup run.
3. Its run ID is explicit freeze/refreeze evidence recorded by the repository documentation.
4. Its status is not `completed`.

The current documented evidence set is:

- `34270011352` — 2026-09-08 cross-suite run.
- `34270610710` — 2026-09-08 freeze-gate run.
- `34457839525` — 2026-09-10 remediation cross-suite revalidation.
- `34458997715` — 2026-09-10 aggregate freeze-candidate run.

Implementation must derive/validate this set from the freeze documentation before deletion rather than silently relying on a stale hand-maintained list.

## Deletion rule

A run is eligible for deletion only when it is `completed`, is not protected by the preservation rules, and belongs to a workflow that is no longer one of the five permanent workflows.

This deliberately removes failed, cancelled, successful, skipped, stale and `action_required` runs from superseded workflow definitions. Their commits remain in Git history; only Actions execution history is deleted.

## Execution mechanism

The normal ChatGPT GitHub connector does not expose the GitHub REST DELETE action for workflow runs. A temporary repository workflow will therefore perform the one-shot cleanup with `GITHUB_TOKEN` and `actions: write` permission.

The temporary workflow is `.github/workflows/cleanup-legacy-runs.yml`. It runs only on a push to `main` that introduces that exact file. It must refuse to execute on any other ref/event, verify all five permanent workflow files exist through the GitHub API, enumerate all workflow runs before deleting any, produce a summary of the keep/delete counts, then delete only the precomputed eligible IDs.

The cleanup must skip its own `github.run_id`. Deletions are sequential or deliberately throttled to reduce secondary-rate-limit risk. Individual 404 responses are treated as already-deleted and may continue; authorization/rate-limit/server errors fail the job.

## Safety and auditability

The cleanup workflow prints the total runs discovered, permanent-workflow runs preserved, evidence runs preserved, non-completed runs preserved and legacy completed runs selected for deletion before the destructive loop begins.

The evidence IDs are checked against the run inventory. A missing historical evidence run is reported but does not broaden deletion eligibility.

The cleanup implementation must not use a date-only cutoff. Workflow identity and explicit evidence are the authoritative criteria.

## Removal after execution

After the cleanup run completes successfully, `.github/workflows/cleanup-legacy-runs.yml` and any helper used only by it are removed in a follow-up repository change. The durable `.github/workflows/` surface returns to exactly five files.

The cleanup run itself may remain as the single maintenance record explaining the bulk deletion.

## Verification

The operation is complete only when:

- `main` contains exactly the five permanent workflows after temporary cleanup files are removed;
- documented evidence run IDs that existed before cleanup still resolve;
- runs belonging to the five permanent workflows are not deleted;
- completed runs belonging to removed legacy workflow definitions are deleted;
- no in-progress/queued run is deleted;
- the cleanup workflow records a final deleted/preserved count;
- the repository integrity/release validation remains green after removing the temporary workflow.
