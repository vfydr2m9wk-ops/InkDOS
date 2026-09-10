# GitHub Actions Workflow Consolidation Design

Date: 2026-09-10
Status: proposed for implementation
Baseline: `main` at `69942e231e75968810b969d7d46fc1ceab901e98`

## Goal

Reduce the active GitHub Actions workflow list from the current phase-oriented set to a small permanent set that a human can understand, without removing test coverage, weakening the frozen baseline, changing application behavior, or deleting historical freeze evidence.

## Scope

This is a CI-organization change only. Test files, application runtime code, frozen feature scope, format-preservation rules, integrity checks, cross-browser coverage, and release semantics remain unchanged unless a mechanical adjustment is required to invoke the same checks from the consolidated workflows.

Historical workflow runs are not deleted by this change. Runs referenced by freeze/refreeze documentation must remain available. The connector used for this change does not expose bulk deletion of Actions run history.

## Target workflow set

The active `.github/workflows/` surface will be reduced to five permanent workflows:

1. `workspace-regression.yml` — all workspace-specific regression and round-trip jobs for Documents, Spreadsheets, Presentations, Plain Text, EPUB and PDF.
2. `integration-regression.yml` — pre-phase architecture and cross-suite/offline/isolation validation.
3. `stability-freeze.yml` — aggregate frozen-baseline and release/freeze validation.
4. `apply-inkdos-update.yml` — the existing operational update workflow, retained as a distinct operational action.
5. `refresh-integrity-metadata.yml` — the existing integrity metadata maintenance workflow, retained as a distinct operational action.

The visible workflow names must be concise and permanent: `Workspace regressions`, `Integration gates`, `Freeze / release`, `InkDOS update`, and `Integrity metadata`.

## Migration mapping

The following phase-specific or duplicated workflow responsibilities move into `workspace-regression.yml`:

- `doc-d1-roundtrip.yml`
- `doc-d2-p1-roundtrip.yml`
- `documents-stability-regression.yml`
- `pdf-stability-regression.yml`
- `epub-stability-regression.yml`
- `presentations-stability-regression.yml`
- `ppt-p1-structure-roundtrip.yml`
- `ppt-p2-regression.yml`
- `spreadsheets-stability-regression.yml`
- `txt-stability-regression.yml`
- `xls-s1-regression.yml`
- `xls-s2-regression.yml`

The following responsibilities move into `integration-regression.yml`:

- `pre-phase-architecture-audit.yml`
- `cross-suite-stability-regression.yml`

The following responsibility moves into `stability-freeze.yml`:

- `stability-freeze-regression.yml`

After equivalent jobs exist in the consolidated workflows and verification passes, the superseded workflow YAML files above are deleted from the branch.

## Trigger semantics

The consolidated workflows must preserve the union of the existing relevant triggers and path filters. Consolidation must not cause expensive browser suites to run on unrelated changes that did not previously trigger them, and it must not stop a check from running for a change that previously required it.

Where phase workflows currently have different path filters, the consolidated workflow should use job-level `if` conditions or a change-detection job so that only applicable workspace jobs execute. Manual dispatch is retained where it already exists and is useful for audit/freeze verification.

## Job organization

`workspace-regression.yml` should expose one clearly named top-level job group per workspace. Documents, Presentations and Spreadsheets may contain multiple sequential steps for their former phase-specific checks, but they appear under the permanent workspace name rather than historical phase names.

Browser matrices remain explicit where the existing gates require Chromium, Firefox or WebKit. Existing Python/static contract checks and package-preservation/round-trip checks are retained.

`integration-regression.yml` contains architecture validation first and cross-suite validation second, with dependencies preserving any existing ordering requirement.

`stability-freeze.yml` remains the authoritative aggregate gate for the frozen baseline and must continue to run the full required validation surface before a freeze/release is considered valid.

## Integrity and automation safety

Because `CHECKSUMS.sha256`, `SOURCE_LOCK.json`, and integrity automation are part of the repository trust model, workflow-file changes must be reconciled through the existing integrity metadata mechanism. No workflow may create an automatic commit loop solely because another workflow file was consolidated.

The existing update and metadata workflows remain separate because they perform repository mutations/maintenance rather than ordinary regression testing.

## Verification

Implementation is acceptable only if all of the following are demonstrated on the consolidation branch:

- the active workflow file count is exactly five;
- every test command formerly invoked by the removed workflows is still invoked by one of the consolidated workflows;
- path/trigger behavior is preserved or made strictly more selective without losing required coverage;
- integrity metadata is refreshed and repository validation passes;
- workspace regression jobs pass for all six workspaces;
- integration/architecture/cross-suite gates pass;
- stability freeze validation passes;
- no application runtime file changes are introduced by the consolidation itself;
- the branch is mergeable into `main`.

## Rollback

If any consolidated gate cannot reproduce the previous behavior, keep the legacy workflow responsible for that gate until parity is proven. Do not delete a legacy workflow merely to hit the target count.

## Expected human-facing result

The GitHub Actions sidebar presents five durable workflow categories instead of many historical phase names. Historical runs remain available for audit evidence, but future runs are grouped under the permanent categories above.
