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
- Formula/paste representability gates: `fcd8bc1093ab8012044f392c38efa8a5beacacc6` and `6af70258f17915938ea2065fe6b4e30bdbb173a0`.
- UTF-16/BOM encoding RED/fix: `060eba634d7f11fa98be0f36ff4b1c6e6329b040` → `5aec957fe55f7c9a50b37481df3e9d6acb45f157`.
- Final validation SHA: `f91b0fa3119932e3d73ed5e8feacca4e3a5296b4`, GitHub Actions run `34742310953`: all eight jobs PASS.

Goal 1 conclusion: **COMPLETE — VERIFIED**.

## Goal 2 completion evidence

The supplied real PowerPoint regression drove the fidelity investigation. Systematic debugging isolated the bare `normAutofit` importer defect and retained the exact real-title geometry regression.

Key checkpoints:

- Isolated normAutofit RED: `22b473f574c7c34912ba8475fce9c7b67cf5d7a3`.
- Minimal fix: `41b58c439a41cab9345e192ac82b05c8778f773d`.
- Real-title synthetic regression retained in `tests/test_pptx_real_title_fidelity_browser.py`.
- Final validation SHA: `2da4badcdd115f8070af976d49b7e4770bc81125`, GitHub Actions run `34747495167`: all eight jobs PASS across repository contracts, round trips and Chromium/Firefox/WebKit regressions.

Goal 2 conclusion: **COMPLETE — VERIFIED**.

## Goal 3 completed subpasses

Goal 3 remains the only active implementation scope. The architecture is one installed InkDOS application/host, no central tab system and no duplicated full executables.

### Routing, associations and native windows

- `6549ab2efcb8d43378865f84a23aafb1b121f1fb` — RED for a single native workspace routing authority.
- `65543f9b05b8b9c7515c97d86d623e721255825c` — GREEN `desktop/workspaces.json` authority.
- `d80ccf31fee6046a0d1f4b8319b88dc39901b09c` — RED requiring Tauri file associations.
- `07c57726518d695a52bd9dcbeea80365fa9711f6` — GREEN `bundle.fileAssociations` while retaining one bundle identity.
- `ad3e8b5008d77335a55f3e9ac696ef49202de42b` — RED for single-instance / one-native-window-per-file routing.
- `76322a43be174cb39b43c291e90602f1487605b5` — baseline contract aligned with `main` + `file-*` native windows.
- Native cross-platform checkpoint: `fe4df581c54f1f20ea1345eb30e42cca331c71bf`, run `34750381423`: Goal 3 contracts plus `cargo check` on Windows, Ubuntu and macOS PASS.

### Workspace launcher authority and host routing

- `129ae31bb04a5eb6bd9752517a4234cf614485c4` — RED launcher contract.
- `bd97f2cc388dcb40f6eae3bf6aa040d3523dc3dc` — `desktop/launchers.json`, six workspace entries, one `InkDOS` executable and canonical workspace icon paths.
- `d73bac04e10b846ae1cff42e579262e467b640d2` — native `--workspace <id>` routing through the shared host.
- `9d5776fe7ac1c56bc4d4456256b3473dfb0813f5` → `c255fe307844581064c4ccb0c6893ee8dc4abb3b` — RED/GREEN for least-privilege capabilities on `workspace-*` windows.
- Pre-packaging launcher/native checkpoint head: `29173cc5c13c8e4a66c9e59637ae1e78d153accd`, run `34752483926`: launcher/routing/native contracts and `cargo check` on Windows, Ubuntu and macOS PASS.

## Goal 3 installed-launcher subpass — current

The previous launcher authority was declarative only. The current TDD subpass requires installer/package integration so workspace entries are actually installed with the exact existing workspace icon visuals.

### Installed launchers baseline

- `8196980dca44c528ec9e0093d7a356512b8373ac` — initial installed-launcher RED.
- `c261fa7981bb393e395f7462746f5f7dc683b746` — NSIS Start Menu workspace shortcuts targeting one shared `InkDOS.exe` with `--workspace <id>`.
- `00f66041816dacfb5c1ae1372cd7023259c5d67e` — MSI/WiX workspace shortcut component group targeting the same shared host.
- Linux launcher entries were added for Documents, Spreadsheets, Presentations, PDF, EPUB and Plain Text.
- `0a0e4ef882bf66a8ac76c1f68d43cdef6397f4a6` — Tauri packaging wiring with explicit `mainBinaryName: "InkDOS"`, NSIS/WiX integration and DEB/RPM/AppImage launcher installation.
- Run `34753566143` for that packaging candidate completed successfully: installed-launcher/routing/native contracts and cross-platform `cargo check` passed.

### Windows exact-icon TDD / systematic-debugging cycle

- `e389391eee05d8be188da9d7efae9bfe270f8d77` — RED requiring workspace-specific native Windows shortcut icons rather than falling back to the shared executable icon.
- `3c9e96b001ba688be8384049fb9f3320ff4b7cd3` — first candidate: NSIS/WiX workspace icon bindings plus `bundle.resources` and a late `beforeBundleCommand` materializer.
- Run `34756160675`: installed-launcher contract passed, but cross-platform `cargo check` failed. Systematic debugging showed Tauri validates `bundle.resources` during its Rust build script before `beforeBundleCommand` can generate those files. The failure was therefore a packaging-order defect, not a Rust host defect.
- `8d42be018eef2d63090f13aef1c359d2b35436a3` — diagnostic/materialization checkpoint. Run `34756409963` successfully generated all six workspace ICOs from the canonical `desktop/launchers.json` icon sources via `cargo tauri icon`; the generation artifact succeeded, while cargo checks still failed as expected because the generated files were not present at config-validation time.
- `ee76f18aaa83e908a41d608b451eda1c4d22740b` — corrected RED contract: require pre-build materialization plus direct NSIS/WiX embedding and prohibit the circular `bundle.resources`/late-hook dependency.
- `f57f3ce9e3c4df59484b32dc6622c693204e6931` — current implementation candidate. It:
  - removes generated workspace ICOs from `bundle.resources` and removes the late `beforeBundleCommand`;
  - keeps `desktop/scripts/generate_workspace_icons.py` as the canonical-source native-icon materializer;
  - makes the production desktop workflow generate the six native workspace icons before both `cargo check` and native bundling;
  - captures the NSIS hook directory at include time and embeds/copies each generated ICO into the installed single InkDOS host before creating the six workspace shortcuts;
  - makes WiX both embed each generated ICO for shortcut display and install it under the single InkDOS installation.
- Exact-head Goal 3 run `34757004301` for `f57f3ce...` is currently pending with zero assigned jobs. No GREEN claim is made until that run actually executes and passes.

Goal 3 therefore remains **IN PROGRESS** and Goal 4 remains locked.

## Goal 3 remaining acceptance work

1. Obtain targeted GREEN for `f57f3ce...`: installed-launcher contract plus Windows/Ubuntu/macOS `cargo check` must pass without the generated-resource ordering regression.
2. Only after that, implement and verify the macOS workspace launch-entry equivalent while retaining one InkDOS installation/host and no duplicated full executables.
3. Verify strict per-workspace allowlists/no-redirect behavior end to end together with installed launch routing.
4. Build and inspect native installer artifacts, then run the coherent Goal 3 repository/cross-platform checkpoint before declaring **COMPLETE — VERIFIED**.

## Current checkpoint

- `main`: `9b1848629e8a86c4513785595014ab32fe168a06`.
- Goal 1: **COMPLETE — VERIFIED**.
- Goal 2: **COMPLETE — VERIFIED** at `2da4badcdd115f8070af976d49b7e4770bc81125`, run `34747495167`.
- Goal 3: **IN PROGRESS**; current Windows exact-icon candidate `f57f3ce9e3c4df59484b32dc6622c693204e6931`, run `34757004301` pending/no jobs assigned at checkpoint time.
- Goal 4: **NOT STARTED**.

At the end of Goal 3, record the exact validation SHA, tests/workflows executed, pass/fail state, release-artifact implications and any remaining blocker before unlocking Goal 4.
