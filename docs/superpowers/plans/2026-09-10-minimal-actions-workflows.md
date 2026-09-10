# Minimal GitHub Actions Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce InkDOS GitHub Actions to the smallest durable workflow set that still protects repository integrity, validates the frozen application, and supports the repository update mechanism.

**Architecture:** Keep three workflows with separate trust boundaries: one read-only comprehensive validation workflow, one integrity-metadata maintenance workflow, and one transactional update workflow. Fold all still-relevant regression commands from legacy phase/workspace workflows into the comprehensive validator, then delete the superseded YAML files.

**Tech Stack:** GitHub Actions YAML, Python 3.11, Node.js, Playwright, existing InkDOS test suite.

**Spec:** `docs/superpowers/specs/2026-09-10-actions-workflow-consolidation-design.md`, adjusted by the user's explicit 2026-09-10 instruction to keep only workflows that remain genuinely necessary.

**Execution branch:** `fix/minimal-actions` (moved from the initial `chore/minimal-actions` branch so the repository's existing integrity-metadata workflow can refresh checksums through its normal `fix/**` trigger).

## Global Constraints

- Do not change application runtime code.
- Preserve `apply-inkdos-update.yml` because it is the repository's transactional update path and security boundary.
- Preserve `refresh-integrity-metadata.yml` because generated hashes/CSP/source locks require a write-isolated maintenance path.
- Preserve and repurpose `stability-freeze-regression.yml` as the permanent comprehensive read-only validator.
- Do not preserve historical phase/workspace workflow files merely for audit history; historical runs and commits remain in GitHub/Git.
- The validator must retain the meaningful coverage formerly supplied by DOC-D1/D2, PPT-P1/P2, XLS-S1/S2, workspace stability, cross-suite, and architecture workflows.

---

### Task 1: Define the permanent validation gate

**Files:**
- Modify: `.github/workflows/stability-freeze-regression.yml`
- Create: `tests/test_minimal_workflow_set_contract.py`

**Interfaces:**
- Consumes: existing `tests/`, `scripts/run_release_validation.py`, `scripts/validate_suite_contracts.py`, `requirements-ci.txt`.
- Produces: one permanent read-only CI gate named `InkDOS validation`.

- [ ] **Step 1: Write the workflow-set contract**

Create a static Python test that asserts the durable workflow set is exactly:

```python
EXPECTED = {
    'apply-inkdos-update.yml',
    'refresh-integrity-metadata.yml',
    'stability-freeze-regression.yml',
}
```

and asserts `stability-freeze-regression.yml` contains the critical coverage commands for release validation, frozen contracts, browser stability, PPT-P2 browser regressions, XLS-S1/S2 browser regressions, PDF extended regressions, PPTX security, and preserved round-trips.

- [ ] **Step 2: Verify the new contract fails before legacy workflow deletion**

Run:

```bash
python tests/test_minimal_workflow_set_contract.py
```

Expected: FAIL because more than three workflow YAML files are still present.

- [ ] **Step 3: Expand the permanent validator**

Update `.github/workflows/stability-freeze-regression.yml` so it:

```yaml
name: InkDOS validation

on:
  workflow_dispatch:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
```

Retain the existing static contract loop and three-browser stability matrix. Add explicit three-browser execution for the non-`*_stability_browser.py` feature regressions formerly owned by phase-specific workflows:

```text
tests/test_pdf_stability_frame.py
tests/test_pdf_stability_comments.py
tests/test_pdf_stability_offline.py
tests/test_pptx_security_browser.py
tests/test_ppt_p2_transitions_browser.py
tests/test_ppt_p2_notes_browser.py
tests/test_ppt_p2_theme_browser.py
tests/test_ppt_p2_tables_browser.py
tests/test_ppt_p2_table_structure_browser.py
tests/test_ppt_p2_table_merge_browser.py
tests/test_ppt_p2_table_format_browser.py
tests/test_ppt_p2_table_style_browser.py
tests/test_ppt_p2_table_tools_ui_browser.py
tests/test_xls_s1_structural_formulas_browser.py
tests/test_xls_s1_structural_columns_browser.py
tests/test_xls_s2_clipboard_browser.py
```

Retain Chromium format-preservation `*roundtrip.py` coverage. Add `python scripts/run_release_validation.py` and `python tests/test_update_trust_boundary.py` to static validation.

- [ ] **Step 4: Validate YAML and static contract locally/CI**

Run at minimum:

```bash
python tests/test_minimal_workflow_set_contract.py
python scripts/run_release_validation.py
```

The first test will remain red until Task 2 removes legacy YAML files; release validation must pass.

- [ ] **Step 5: Commit**

Commit the validator and contract together.

---

### Task 2: Remove superseded workflow definitions

**Files:**
- Delete: `.github/workflows/cross-suite-stability-regression.yml`
- Delete: `.github/workflows/doc-d1-roundtrip.yml`
- Delete: `.github/workflows/doc-d2-p1-roundtrip.yml`
- Delete: `.github/workflows/documents-stability-regression.yml`
- Delete: `.github/workflows/epub-stability-regression.yml`
- Delete: `.github/workflows/pdf-stability-regression.yml`
- Delete: `.github/workflows/ppt-p1-structure-roundtrip.yml`
- Delete: `.github/workflows/ppt-p2-regression.yml`
- Delete: `.github/workflows/pre-phase-architecture-audit.yml`
- Delete: `.github/workflows/presentations-stability-regression.yml`
- Delete: `.github/workflows/spreadsheets-stability-regression.yml`
- Delete: `.github/workflows/txt-stability-regression.yml`
- Delete: `.github/workflows/xls-s1-regression.yml`
- Delete: `.github/workflows/xls-s2-regression.yml`

**Interfaces:**
- Consumes: coverage migrated in Task 1.
- Produces: exactly three durable workflow YAML files.

- [ ] **Step 1: Delete only the superseded workflow YAML files listed above**

Do not delete either operational workflow or the aggregate validator.

- [ ] **Step 2: Run the workflow-set contract**

Run:

```bash
python tests/test_minimal_workflow_set_contract.py
```

Expected: PASS and exactly three workflow files detected.

- [ ] **Step 3: Run release/static validation**

Run:

```bash
python scripts/run_release_validation.py
python tests/test_update_trust_boundary.py
```

Expected: PASS.

- [ ] **Step 4: Verify the diff contains no application runtime changes**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected paths are limited to `.github/workflows/**`, `tests/test_minimal_workflow_set_contract.py`, `tests/test_pdf_stability_offline_contract.py`, integrity metadata generated by the standard refresh workflow, and this plan/spec documentation.

- [ ] **Step 5: Commit**

Commit the workflow deletions.

---

### Task 3: Validate on GitHub before merging

**Files:**
- No new runtime files.

**Interfaces:**
- Consumes: branch from Tasks 1-2.
- Produces: evidence that the single validator can replace the deleted workflows.

- [ ] **Step 1: Open a PR from `fix/minimal-actions` to `main`**

- [ ] **Step 2: Confirm `InkDOS validation` runs on the PR**

Verify all jobs complete successfully, including Chromium, Firefox, WebKit, feature-browser regressions, static contracts, and preservation round-trips.

- [ ] **Step 3: Confirm the PR diff has no application runtime changes**

- [ ] **Step 4: Merge only after all validation jobs are green**

- [ ] **Step 5: Re-read `.github/workflows/` on `main`**

Expected durable files:

```text
apply-inkdos-update.yml
refresh-integrity-metadata.yml
stability-freeze-regression.yml
```

The historical Actions-run cleanup is a separate destructive maintenance step and must occur only after this consolidation is proven on `main`.
