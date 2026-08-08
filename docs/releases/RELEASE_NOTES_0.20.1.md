# InkDesk 0.20.1 — Consistency Refinement 1

This patch begins the refinement and stabilization phase after 0.20.0.

## Corrected regressions

- Documents once again exposes Home as the first title-bar action.
- Presentations exposes Home both before opening a file and in the editor title bar.
- Spreadsheet click-and-drag once again selects a continuous cell range.
- Formula reference selection only captures grid pointer events while a formula cursor is in a reference-accepting position.

## Release gate

Loss of an existing function, inconsistent equivalent controls, stale version/cache state, or a failed regression test blocks the patch. The package includes unit and Chromium checks dedicated to Home navigation and spreadsheet selection.

## Corrected package validation

- Every workspace now declares an explicit local favicon, preventing Chromium
  from requesting a missing root `favicon.ico` during module navigation.
- The launch/offline browser gate now reports the exact URL and HTTP status for
  failed resources instead of only Chromium's generic console message.
- This is a packaging correction for v0.20.1; the public version and sequence
  remain unchanged because the previous transaction rolled back.


### Release-integrity correction

- Treat `DEVELOPMENT_STATE.json` as mutable updater state rather than an immutable release artifact.
- Exclude it from checksum generation and verification.
- Add a permanent regression test for sequence updates followed by checksum validation.

## Stable update workflow

- Update ZIPs can no longer create, modify, or delete GitHub workflow files.
- The workflow is a one-time manual bootstrap and remains stable afterward.
- The root ZIP is retained until validation succeeds.
- The Actions summary is written after the commit/push step and distinguishes
  validation failure from push failure.
- Checkout and Python setup use Node 24-compatible action generations.
- A Pages rebuild is requested explicitly after a successful update push.
