# InkDOS 2.3 Implementation Checkpoint

## Canonical state

- Canonical spec: `docs/superpowers/specs/2026-09-13-inkdos-2.3-design.md`
- Approval: `USER-APPROVED`
- Current `main`: `690021d6577b7eb337016e0d19af9310fd6f424a`
- Canonical development branch: `feature/inkdos-2.3`
- Open development PR: #132
- Fixed sequence: Goal 1 → Goal 2 → Goal 3 → Goal 4. Do not restart or reorder.

## Sequence state

1. Goal 1 — editable format coverage: **COMPLETE — VERIFIED — IN MAIN**
2. Goal 2 — PPTX/PowerPoint fidelity: **COMPLETE — VERIFIED — IN MAIN**
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
- Promoted to `main` in the verified web checkpoint ending at `690021d6577b7eb337016e0d19af9310fd6f424a`.

Goal 1 conclusion: **COMPLETE — VERIFIED — IN MAIN**.

## Goal 2 completion evidence

The supplied real PowerPoint regression drove the fidelity investigation. Systematic debugging isolated the bare `normAutofit` importer defect and retained the exact real-title geometry regression.

Key checkpoints:

- Isolated normAutofit RED: `22b473f574c7c34912ba8475fce9c7b67cf5d7a3`.
- Minimal fix: `41b58c439a41cab9345e192ac82b05c8778f773d`.
- Real-title synthetic regression retained in `tests/test_pptx_real_title_fidelity_browser.py`.
- Final validation SHA: `2da4badcdd115f8070af976d49b7e4770bc81125`, GitHub Actions run `34747495167`: all eight jobs PASS across repository contracts, round trips and Chromium/Firefox/WebKit regressions.
- Promoted to `main`; main validation run `34760424237` is the verified post-promotion web checkpoint.

Goal 2 conclusion: **COMPLETE — VERIFIED — IN MAIN**.

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

### Installed launchers and exact icons

- `8196980dca44c528ec9e0093d7a356512b8373ac` — initial installed-launcher RED.
- `c261fa7981bb393e395f7462746f5f7dc683b746` — NSIS Start Menu workspace shortcuts targeting one shared `InkDOS.exe` with `--workspace <id>`.
- `00f66041816dacfb5c1ae1372cd7023259c5d67e` — MSI/WiX workspace shortcut component group targeting the same shared host.
- Linux launcher entries were added for Documents, Spreadsheets, Presentations, PDF, EPUB and Plain Text.
- `0a0e4ef882bf66a8ac76c1f68d43cdef6397f4a6` — Tauri packaging wiring with explicit `mainBinaryName: "InkDOS"`, NSIS/WiX integration and DEB/RPM/AppImage launcher installation.
- Run `34753566143` completed successfully for that packaging baseline.
- `e389391eee05d8be188da9d7efae9bfe270f8d77` — RED requiring workspace-specific Windows shortcut icons.
- `3c9e96b001ba688be8384049fb9f3320ff4b7cd3` — first candidate; systematic debugging of run `34756160675` isolated a Tauri packaging-order defect: generated `bundle.resources` were validated before `beforeBundleCommand` could create them.
- `8d42be018eef2d63090f13aef1c359d2b35436a3` / run `34756409963` proved all six native workspace ICOs can be generated from the canonical launcher icon sources.
- `ee76f18aaa83e908a41d608b451eda1c4d22740b` — corrected RED requiring pre-build materialization/direct embedding and prohibiting the circular late-hook dependency.
- `f57f3ce9e3c4df59484b32dc6622c693204e6931` — corrected Windows exact-icon implementation candidate. Its run `34757004301` subsequently completed GREEN.

### macOS launch entries

- `36b48656365e1441fd882d665152738168fb8ae1` — RED for macOS workspace launch entries.
- `2108f284d6a599d83eb8f6dff8d1d0d2c6e2d0e2` — registers the macOS launcher contract in the Goal 3 checkpoint workflow.
- `9dcc164605bcfad388c87d6470a2a5616f14c286` — generator for six minimal helper launch bundles under the single InkDOS application host.
- `e01aaeebf918387e7d5abc35c8f431153bda9050` and `bf4cd722e9d65661ef03aeef1939a3cf15771801` — Tauri/production packaging integration.
- `7de57294d024e81fcbf8d2f398e4ba0644bf7521` — native verification for six launcher executables, six `Info.plist` files and six canonical `icon.icns` files.
- Run `34760575409` confirmed Windows icon materialization and macOS launcher materialization GREEN. That run's contract job was RED only because the next strict-allowlist test had already been introduced.

### Strict workspace allowlist / no-reroute cycle — current

- `7cbae6aac57ff08c88692b2a3f422f6617796a79` — RED extending `tests/test_tauri_goal3_native_window_contract.py` so workspace launcher file arguments must remain bound to that workspace's allowlist and must not silently reroute.
- Run `34760575409` reproduced the RED specifically in `Run native multiwindow contract`; launcher materialization remained GREEN.
- Root cause: `handle_launch_args` opened `--workspace <id>` but then processed following file paths through the global `open_file_window`, allowing extension-based routing to a different workspace.
- `f5f1e63932ffe2ab0a22e8d1b0809dbc1848720a` — minimal fix: preserve an `active_workspace`, validate files through `workspace_supports_path`, and open them with `open_file_window_for_workspace`; global routing remains only for file opens without a workspace context.
- Run `34761367400`: the Goal 3 contracts job is GREEN, including workspace/association, workspace launcher, installed launcher, macOS launcher, native multiwindow, baseline desktop and staged-runtime checks. Icon/macOS materialization and cross-platform cargo jobs were still running at this checkpoint, so the full run is not yet claimed GREEN.

Goal 3 therefore remains **IN PROGRESS** and Goal 4 remains locked.

## Goal 3 remaining acceptance work

1. Obtain the completed result for run `34761367400`, including Windows/Ubuntu/macOS `cargo check` after the strict-allowlist fix.
2. Exercise/verify strict per-workspace allowlists and no-reroute behavior together with installed launch routing at the strongest practical native test level.
3. Build and inspect Windows/macOS/Linux installer/package artifacts, including installed launch entries/icons and one-host/no-duplicate-executable constraints.
4. Run the coherent Goal 3 repository/cross-platform checkpoint and record the exact final validation SHA/run before declaring **COMPLETE — VERIFIED**.
5. Only then unlock Goal 4.

## Current checkpoint

- `main`: `690021d6577b7eb337016e0d19af9310fd6f424a`.
- Goal 1: **COMPLETE — VERIFIED — IN MAIN**.
- Goal 2: **COMPLETE — VERIFIED — IN MAIN**.
- Goal 3: **IN PROGRESS**; strict workspace allowlist fix candidate `f5f1e63932ffe2ab0a22e8d1b0809dbc1848720a`; run `34761367400` has a GREEN contracts job while native materialization/cross-platform validation remains in progress at checkpoint time.
- Goal 4: **NOT STARTED**.

At the end of Goal 3, record the exact validation SHA, tests/workflows executed, pass/fail state, release-artifact implications and any remaining blocker before unlocking Goal 4.
