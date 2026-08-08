# InkDesk v0.20.2.2 — Refactoring Guardrails

InkDesk v0.20.2.2 starts the architecture-hardening phase without adding or
removing editor functions. The purpose of this patch is to make future
refactoring safer for both AI-assisted and human development.

## Added

- `AGENTS.md` with smallest-scope, zero-regression, visual, local-first and
  update-package rules.
- `architecture-policy.json` recording the v0.20.2.1 source-debt baseline.
- `scripts/check_architecture_guardrails.py` as a permanent quality gate.
- Checks that new runtime JS/CSS stays focused and readable while existing debt
  may shrink but not grow.
- Runtime dependency checks for cross-workspace imports, shared-to-app imports
  and relative module cycles.
- An explicit native-module ADR: no React/framework migration during the 0.20.x
  behavior-neutral refactor.
- An ordered refactoring sequence: Presentations, PDF, shared UI, then
  Documents/Spreadsheets consolidation.

## Behavior

No editing command, supported format, file lifecycle, recovery behavior or
visual layout is intentionally changed by this release. Any runtime difference
is a regression and blocks the next extraction release.

## Correction 2 — checksum lineage

Hosted validation confirmed 226/226 unit/package tests and 12/12 Chromium browser regressions, then exposed one stale checksum entry for `shared/vendor/pdfjs/README.md`, which is absent from the accepted repository tree. The stale entry is removed. A permanent fail-fast unit regression now runs the repository checksum verifier before browser regressions are reached. No application runtime behavior changes in this correction.
