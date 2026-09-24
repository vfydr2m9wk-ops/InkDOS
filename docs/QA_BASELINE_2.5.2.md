# InkDOS 2.5.2 stable QA baseline

InkDOS 2.5.2 is the immutable stable baseline published from tag `v2.5.2`, which points to commit `3470607f440d34b361aff4a790acec442d84fb56`.

This document preserves the useful conclusions from the final 2.5.2 verification so obsolete GitHub Actions runs can be pruned without losing the maintenance decision record.

## Final verification

- Full clean-snapshot release validation: PASS.
- Tauri desktop contract/staging validation at the tagged candidate: PASS.
- GitHub Pages deployment at the tagged candidate: PASS.
- Native release transaction: PASS for Windows, macOS and Linux.
- Signed updater/release provenance validation: PASS.
- Chromium online matrix after the final toolbar fixes: 336 cases, zero JavaScript-error cases, zero HTTP failures, zero root-overflow cases and zero click exceptions.
- WebKit online matrix: 336 cases with no JavaScript-error, HTTP-failure or root-overflow findings in the completed matrix audit.
- Stateful active-control audit after the final Presentations/PDF hitbox repairs: zero JavaScript-error apps and zero surface failures.
- Behavioral stability/soak gate: PASS with repeated stateful cycles across the suite.

## Regressions closed before freeze

The final audit directly identified and closed:
- Presentations background-color input escaping its wrapper and intercepting Zoom/Present controls.
- PDF icon-only Organize control overflowing into the preceding navigation hitbox.
- Earlier disabled Presentations background input interception.
- Plain Text recovery isolation between tabs.

These fixes are included in the tagged 2.5.2 baseline.

## Preservation policy

The tag/release is the historical source of truth for the stable product. Post-release work on `main` may improve CI, documentation and development process without changing the tagged baseline.

Legacy Actions runs are not the primary source of truth once their result has been captured here and the corresponding regression tests/audit harnesses are preserved in the repository.
