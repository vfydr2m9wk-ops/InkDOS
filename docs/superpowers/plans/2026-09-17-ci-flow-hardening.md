# InkDOS CI Flow Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent green PRs from becoming red only after merge by unifying architecture policy and running the same full integrity gate before and after merge.

**Architecture:** A single JSON policy defines approved shared presentation runtime. Both architecture validators import one helper for that policy. A dedicated read-only integrity workflow runs on PR/main, while update-package application remains manual-only.

**Tech Stack:** Python 3.11, GitHub Actions YAML, existing Playwright/Node validation dependencies.

**Spec:** `docs/superpowers/specs/2026-09-17-ci-flow-hardening-design.md`

## Global Constraints

- Preserve released `v2.3.0` tag/release.
- Do not publish a public InkDOS 2.4 release.
- Do not alter editor/runtime feature behavior, functional IDs/actions/parsers/formulas/serialization/user content.
- Keep update-package write permissions isolated to the manual apply job.

---

### Task 1: Add the CI flow contract and pre-merge full gate

**Files:**
- Create: `tests/test_ci_flow_contract.py`
- Create: `.github/workflows/ci-integrity.yml`

**Interfaces:**
- Consumes: existing `scripts/run_release_validation.py` and metadata generator.
- Produces: one read-only integrity gate used on PR and `main`.

- [ ] **Step 1: Write the failing contract**

Assert that a central shared-runtime policy exists, both validators consume it, `ci-integrity.yml` runs the complete gate on PR/main, and `apply-inkdos-update.yml` is manual-only.

- [ ] **Step 2: Run on the PR merge ref and verify RED**

Expected: FAIL because the central policy/helper do not exist and the update workflow still owns the push validation job.

- [ ] **Step 3: Keep the CI workflow read-only**

Use `permissions: contents: read`, install existing CI requirements, verify generated metadata, run the CI flow contract, then `scripts/run_release_validation.py`.

### Task 2: Centralize approved shared runtime

**Files:**
- Create: `config/shared-runtime-policy.json`
- Create: `scripts/shared_runtime_policy.py`
- Modify: `scripts/check_no_legacy_runtime.py`
- Modify: `scripts/validate_app_isolation.py`

**Interfaces:**
- Produces: `is_allowed_shared_relpath(relpath: str) -> bool`.
- Consumed by: both architecture validators.

- [ ] **Step 1: Add policy data**

Allow exact `ui-density.js` / `ui-density.css` and prefix `localization/`; reject all other shared paths by default.

- [ ] **Step 2: Add trusted helper**

Load and validate JSON policy, normalize POSIX relative paths, reject traversal/absolute paths, and expose the boolean predicate.

- [ ] **Step 3: Replace duplicated allowlists**

Use the helper in both architecture validators; remove their private shared-runtime allowlists.

- [ ] **Step 4: Verify GREEN for the policy contract**

Expected: the current approved localization subtree is accepted while an arbitrary shared runtime remains rejected.

### Task 3: Separate ordinary CI from update-package application

**Files:**
- Modify: `.github/workflows/apply-inkdos-update.yml`

**Interfaces:**
- `ci-integrity.yml`: read-only PR/main validation.
- `apply-inkdos-update.yml`: manual package validation/application only.

- [ ] **Step 1: Remove push trigger and ordinary validate job**

Retain `workflow_dispatch`, `validate-update`, and `apply-update` trust boundaries.

- [ ] **Step 2: Rename workflow clearly**

Use a name that communicates manual package application rather than general integrity validation.

- [ ] **Step 3: Run CI flow contract**

Expected: PASS.

### Task 4: Full verification and integration

**Files:** none beyond Tasks 1-3.

- [ ] **Step 1: Run complete integrity gate on PR merge ref**

Expected: metadata check clean; CI-flow contract PASS; `scripts/run_release_validation.py` exit 0.

- [ ] **Step 2: Confirm application-specific validation remains green**

Existing localization/browser validation must remain green where triggered.

- [ ] **Step 3: Merge only after fresh green evidence**

After merge, verify `main` runs the same `ci-integrity.yml` gate successfully and that the `v2.3.0` release/tag remain unchanged.
