# InkDOS 2.3 Implementation Checkpoint

## Canonical state

- Canonical spec: `docs/superpowers/specs/2026-09-13-inkdos-2.3-design.md`
- Approval: `USER-APPROVED`
- Current `main`: `9b1848629e8a86c4513785595014ab32fe168a06`
- Canonical development branch: `feature/inkdos-2.3`
- Open development PR: #132
- Fixed sequence: Goal 1 → Goal 2 → Goal 3 → Goal 4. Do not restart or reorder.

## Sequence state

1. Goal 1 — editable format coverage: **COMPLETE — VERIFIED**
2. Goal 2 — PPTX/PowerPoint fidelity: **COMPLETE — VERIFIED**
3. Goal 3 — desktop associations/launchers/native windows: **IN PROGRESS**
4. Goal 4 — manual-only updater: **NOT STARTED**

## Development cadence

- TDD remains mandatory: targeted RED first, minimal implementation, then GREEN.
- Use systematic debugging for defects.
- Run coherent Goal-sized repository/cross-platform validation before declaring a Goal complete.
- Keep the PR draft while InkDOS 2.3 is incomplete.
- Preserve local-first/no telemetry/no backend behavior.
- Do not begin Goal 4 until Goal 3 is COMPLETE — VERIFIED.

## Goal 1 completion evidence

Goal 1 retained the approved Plain Text family and CSV/TSV spreadsheet behavior, including same-extension save, quoted fields, embedded delimiters/newlines, BOM/encoding preservation, leading-zero strings, explicit XLSX conversion guards, formula/paste representability guards, and unsupported-format rejection.

Key preserved checkpoints:

- Initial Plain Text RED: `14edf384fee683c6f59817ef9c3a652c1c9515fa`.
- CSV/TSV codec RED: `d523b830837ff661637c51916cd44df42d6b1e8f`.
- CSV/TSV codec GREEN: `d3039d7497f4e0a67c4f89b3ac544947a2c5fcc6`.
- CSV/TSV integration RED: `1943f332c04874d288350468ac5e70b122b1189e`.
- Formula Bar conversion gate: `fcd8bc1093ab8012044f392c38efa8a5beacacc6`.
- Grid/paste/formula representability gates: `6af70258f17915938ea2065fe6b4e30bdbb173a0`.
- UTF-16/BOM encoding RED: `060eba634d7f11fa98be0f36ff4b1c6e6329b040`.
- Encoding MIME fix: `5aec957fe55f7c9a50b37481df3e9d6acb45f157`.
- Main ancestry reconciliation: `addaa0d707835b072925ae5926684f87823f9fa9`.

Final Goal 1 validation:

- Validation SHA: `f91b0fa3119932e3d73ed5e8feacca4e3a5296b4`.
- GitHub Actions run: `34742310953`.
- Result: all eight jobs PASS, including repository contracts, clean-snapshot validation, Chromium/Firefox/WebKit stability, Chromium/Firefox/WebKit feature regressions, and format-preservation round trips.
- Post-validation CI-policy restoration: `fffc187e4bc819e33e17f28f5a4a39c2e12b7ec9`; runtime/product/test content was unchanged.

Goal 1 conclusion: **COMPLETE — VERIFIED**.

## Goal 2 completion evidence

The supplied real PowerPoint regression was used to drive the fidelity investigation. Slide 1's title uses three Arial Bold 112.5 pt runs, `spc=-337`, 92% line spacing, 2 pt insets, a U+00AD soft hyphen, and bare `normAutofit`.

Systematic debugging isolated a concrete importer defect: bare `normAutofit` has no `fontScale`, but the importer treated the missing value as zero and clamped it to 0.35, incorrectly shrinking text and tracking.

Key checkpoints:

- Isolated normAutofit RED head: `22b473f574c7c34912ba8475fce9c7b67cf5d7a3`.
- Minimal normAutofit fix: `41b58c439a41cab9345e192ac82b05c8778f773d`.
- Focused fix run: `34746864039` — PASS.
- Real-title synthetic regression: `tests/test_pptx_real_title_fidelity_browser.py`, frozen from the real slide metrics rather than an approximation.
- Exact real-title run: `34747079211` — PASS, retaining three runs, U+00AD soft hyphen, `spc=-337` / `-3.37px` tracking, 92% line spacing, scale 1, and expected two-line geometry.
- Superseded one-shot diagnostics removed in `df809a3320f749c46b2acbd6cb9bc92ae7454791`.

Final Goal 2 validation:

- Validation SHA: `2da4badcdd115f8070af976d49b7e4770bc81125`.
- GitHub Actions run: `34747495167`.
- Result: all eight jobs PASS, including repository contracts, format round trips, Chromium/Firefox/WebKit stability, and feature regressions with the retained PowerPoint fidelity regressions on all three engines.

Goal 2 conclusion: **COMPLETE — VERIFIED**. Goal 3 was not started before this validation passed.

## Goal 3 current work

Goal 3 is now the only active implementation scope. The architecture remains one installed InkDOS application/host, with no central tab system and no duplicated full executables.

TDD checkpoints completed so far:

- `6549ab2efcb8d43378865f84a23aafb1b121f1fb` — RED contract establishing a single native workspace routing authority. RED was reproduced because `desktop/workspaces.json` did not exist.
- `65543f9b05b8b9c7515c97d86d623e721255825c` — GREEN implementation of `desktop/workspaces.json`, mapping each approved extension to exactly one workspace, route, and the existing workspace icon path.
- `d80ccf31fee6046a0d1f4b8319b88dc39901b09c` — RED contract requiring Tauri bundle file associations to match the workspace authority. RED was reproduced because `bundle.fileAssociations` was absent.
- `07c57726518d695a52bd9dcbeea80365fa9711f6` — GREEN Tauri `bundle.fileAssociations` registration for Documents, Spreadsheets, Presentations, PDF, EPUB, and Plain Text extension families while retaining one `InkDOS` product/bundle identifier.
- `c98c51cd2c1e81f47ebf26154dbb65b112c848f9` — registers the Goal 3 routing/association contract in `scripts/run_release_validation.py`.

Focused local contract probes observed the routing authority RED/GREEN and the Tauri association RED/GREEN transitions. A coherent Goal 3 native-runner checkpoint has not yet been run and Goal 3 is therefore not complete.

## Goal 3 remaining acceptance work

Continue Goal 3 only, in TDD order:

1. Native launch routing for associated files with strict extension rejection and a clear unsupported-format notification.
2. One native window per opened file, including subsequent opens while InkDOS is already running, while retaining one application host/installation.
3. Workspace-specific installed launch entries using the existing workspace icons exactly; no six-installation or duplicate-executable model.
4. Per-workspace allowlist verification end to end, including no redirect on unsupported extension.
5. Native/cross-platform build and repository checkpoint validation before declaring Goal 3 COMPLETE — VERIFIED.

## Current checkpoint

- `main`: `9b1848629e8a86c4513785595014ab32fe168a06`.
- Goal 1: **COMPLETE — VERIFIED**.
- Goal 2: **COMPLETE — VERIFIED** at `2da4badcdd115f8070af976d49b7e4770bc81125`, run `34747495167`.
- Goal 3: **IN PROGRESS**.
- Goal 4: **NOT STARTED**.

At the end of Goal 3, record the exact validation SHA, tests/workflows executed, pass/fail state, release-artifact implications, and any remaining blocker before unlocking Goal 4.
