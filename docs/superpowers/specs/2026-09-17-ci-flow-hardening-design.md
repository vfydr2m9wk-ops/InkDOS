# InkDOS CI Flow Hardening Design

## Problem

InkDOS currently has different pre-merge and post-merge gates. InkDOS 2.4 passed its PR-specific localization/browser validation, but after merge the global `InkDOS integrity and update` workflow failed because `scripts/check_no_legacy_runtime.py` still treated the approved `shared/localization/**` presentation layer as forbidden cross-suite runtime. This creates a late-failure pattern: a PR can be green while the same merge becomes red on `main`.

The architecture policy is also duplicated. `check_no_legacy_runtime.py` and `validate_app_isolation.py` each maintain their own shared-runtime allowlist, so an approved architectural change can update one gate but not the other. Finally, `.github/workflows/apply-inkdos-update.yml` combines ordinary repository validation with the privileged/manual update-package path, making failures harder to classify.

## Goals

1. Run the complete repository integrity gate on pull requests before merge and again on pushes to `main`.
2. Make approved shared presentation runtime a single source of truth.
3. Keep `shared/ui-density.*` and `shared/localization/**` explicitly approved while rejecting unknown shared runtime.
4. Separate read-only CI from the manual update-package workflow.
5. Preserve the released `v2.3.0` tag/release and the already-integrated InkDOS 2.4 application code.
6. Do not publish a public InkDOS 2.4 release.

## Non-goals

- No editor/runtime feature changes.
- No changes to functional IDs, actions, parsers, formulas, serialization, or user content.
- No release publication or updater signing operation.
- No broad rewrite of the desktop release workflow in this change; release preflight/build/publish optimization remains a separate follow-up after the integrity gate is stable.

## Architecture

### Central shared-runtime policy

Add `config/shared-runtime-policy.json` as the canonical policy. It authorizes exact shared files for UI density and the dedicated `localization/` presentation-only subtree. A small repository-trusted helper, `scripts/shared_runtime_policy.py`, loads and validates that policy and exposes `is_allowed_shared_relpath()`.

Both `scripts/check_no_legacy_runtime.py` and `scripts/validate_app_isolation.py` consume this helper instead of maintaining independent allowlists. Unknown files elsewhere under `shared/` remain rejected.

### CI integrity workflow

Add `.github/workflows/ci-integrity.yml` with read-only permissions. It runs on `pull_request`, on pushes to `main`, and manually via `workflow_dispatch`. The same job used before merge and after merge will:

- install validation dependencies;
- verify generated release metadata is current;
- run the CI-flow contract;
- run `scripts/run_release_validation.py`.

This makes the pull-request merge ref the primary integration gate and prevents a PR from being considered green when the global repository policy would reject it after merge.

### Manual update workflow

`.github/workflows/apply-inkdos-update.yml` becomes manual-only (`workflow_dispatch`). Its package validation and apply jobs remain unchanged in trust boundaries: candidate validation is read-only, while the write-capable apply job runs only after successful validation of immutable package bytes/base SHA.

The ordinary `push: main` validation job is removed from this workflow because it moves to `ci-integrity.yml`.

## Testing

`tests/test_ci_flow_contract.py` will verify:

- the central policy permits `ui-density.js`, `ui-density.css`, and representative localization files;
- unknown shared runtime is rejected;
- both architecture validators import the central policy helper rather than defining independent allowlists;
- `ci-integrity.yml` is configured for PR + `main` push and invokes the full release validation;
- `apply-inkdos-update.yml` is manual-only and no longer contains the ordinary repository validation job.

The new CI workflow itself provides end-to-end verification by running the full existing release-validation suite on the PR merge ref.

## Acceptance criteria

- A PR containing the currently approved `shared/localization/**` architecture passes the global integrity gate.
- Adding an unapproved file such as `shared/arbitrary-runtime.js` remains rejected by policy tests.
- The same full integrity command runs before merge and after merge.
- Update-package application remains manual and write-scoped.
- No application behavior or public release state changes.
