# InkDOS 2.3 Goal 4 Manual Desktop Updater — Implementation Plan

> **Execution note:** This plan implements the user-approved order amendment in `docs/superpowers/specs/2026-09-13-goal4-before-goal3-completion-amendment.md`. Goal 3 is preserved at `c68566ee53010784f63aa915ef1eea575c9762b0` while Goal 4 is implemented. Installed updater E2E validation intentionally waits until Goal 3 packages are finalized.

**Goal:** Add a fail-closed, manual-only, desktop/Tauri updater that checks only on explicit user action, presents current/latest version and release notes, installs only after confirmation, and uses signed Tauri v2 updater artifacts published from the tagged release workflow.

**Architecture:** Keep the web/PWA runtime unchanged. The already desktop-only `desktop/desktop-host.js` bridge owns the update UI and invokes two Rust commands in the Tauri host. Rust owns updater network and install operations through `tauri-plugin-updater`. Release automation enables Tauri updater artifacts, signs them with repository secrets, and publishes a static `latest.json` alongside the native release assets. The private signing key never enters the repository. The public updater key is supplied to Tauri configuration through a committed public-key value once generated; until then configuration/tests must fail closed rather than accepting unsigned artifacts.

**Tech stack:** Tauri v2, Rust, static HTML/CSS/JS, GitHub Actions, Python contract tests.

---

## Task 1 — Establish Goal 4 contract tests (RED)

**Files:**
- Create: `tests/test_goal4_desktop_updater_contract.py`
- Modify only if required for test execution: `.github/workflows/goal4-updater-checkpoint.yml`

**Test requirements:**
1. `desktop/src-tauri/Cargo.toml` must depend on `tauri-plugin-updater = "2"`.
2. `desktop/src-tauri/src/main.rs` must register the updater plugin and expose explicit `check_for_updates` and `install_update` commands.
3. There must be no updater check in `.setup(...)`, startup code, timer, interval, or background task.
4. `desktop/desktop-host.js` must expose an explicit `Check for updates` control only after the Tauri bridge is active.
5. Web/PWA `index.html` and shared runtime must not load updater code or contain an active updater network path.
6. The Tauri config must enable signed updater artifacts and provide updater endpoint/public-key configuration.
7. Release workflow must provide signing secrets only to native build steps and publish `latest.json` plus updater signatures/artifacts.
8. The updater endpoint must be the public GitHub Releases static metadata URL for InkDOS, not a custom backend.

**RED verification:** Run `python tests/test_goal4_desktop_updater_contract.py` and confirm failure because updater plugin/config/UI are not yet present.

## Task 2 — Add the Tauri updater backend (GREEN)

**Files:**
- Modify: `desktop/src-tauri/Cargo.toml`
- Modify: `desktop/src-tauri/src/main.rs`
- Modify: `desktop/src-tauri/tauri.conf.json`
- Modify: `desktop/src-tauri/capabilities/default.json` only if plugin permissions are required by the chosen command architecture.

**Implementation:**
1. Add `tauri-plugin-updater = "2"` and serde support needed for command responses.
2. Register `tauri_plugin_updater::Builder::new().build()`.
3. Add a serializable update-check response containing installed version, available version, release notes/date when present, and an `available` boolean.
4. `check_for_updates` performs the first network request only when invoked by the UI. It calls the configured updater endpoint and returns a normalized response. No startup task calls it.
5. `install_update` is a separate explicit command. It rechecks/fetches through the updater trust boundary and installs only the update version the user explicitly approved. If the version changed between check and install, fail closed and ask the user to check again rather than silently installing a different release.
6. Enable `bundle.createUpdaterArtifacts` and configure `[plugins.updater]` JSON equivalent with the GitHub Releases `latest.json` endpoint and committed public verification key.
7. Do not add automatic relaunch behavior unless required for the current platform. Windows may exit as part of installer behavior; macOS/Linux may instruct the user to relaunch after successful installation.

**Verification:**
- `cargo check` in `desktop/src-tauri`
- `python tests/test_goal4_desktop_updater_contract.py`

## Task 3 — Add desktop-only updater UI (RED → GREEN)

**Files:**
- Modify: `desktop/desktop-host.js`
- Modify: `assets/home.css` only if the injected control needs shared styling; prefer styles scoped/injected by desktop host to keep web/PWA unchanged.
- Create: `tests/test_goal4_updater_ui_browser.py`

**RED behavior test:**
1. In ordinary web/PWA page load, no update button/modal/network request exists.
2. In a simulated Tauri bridge, the desktop host adds one update control with tooltip/accessible label `Check for updates`.
3. Clicking it invokes only the check command.
4. Current-version response shows installed/latest and `You're using the latest version.`
5. Available-update response shows installed/latest, release notes, `Install`, and `Cancel`.
6. `Install` invokes install only after explicit click; `Cancel` invokes nothing.
7. Errors remain in the modal and do not trigger automatic retry/polling.
8. No `setInterval`, startup updater invocation, or automatic network operation is present.

**Implementation:**
- Inject the control and modal only from `desktop/desktop-host.js` after Tauri detection.
- Use `window.__TAURI__.core.invoke` for Rust commands.
- Keep update state local to the current desktop window; no backend/telemetry/state service.
- Disable duplicate clicks while a command is in flight.
- Escape/render release notes as text, not trusted HTML.

**Verification:** Run focused browser test in Chromium, Firefox, and WebKit where feasible for DOM logic, plus static contract. Native invocation itself is covered by Rust/contract testing until installed E2E.

## Task 4 — Build signed release/update publication path (TDD)

**Files:**
- Modify: `.github/workflows/release.yml`
- Create: `desktop/scripts/build_updater_manifest.py` only if Tauri CLI does not directly emit final static metadata in the exact required shape.
- Create/modify: `tests/test_goal4_release_updater_contract.py`
- Update: `docs/UPDATE_MODEL.md`

**Requirements:**
1. Native build jobs receive `TAURI_SIGNING_PRIVATE_KEY` and `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` from GitHub Actions secrets only; never echo them.
2. `createUpdaterArtifacts` causes platform updater packages/signatures to be emitted from the same tagged source as installers.
3. Publish job downloads updater artifacts and validates one coherent version across all platforms.
4. Generate a deterministic Tauri-compatible static `latest.json` referencing immutable assets from the same GitHub release tag.
5. `latest.json` includes version, release notes/date, per-platform URL/signature fields and is uploaded as a release asset.
6. Fail if signatures/updater packages are absent, duplicated, inconsistent, or version-mismatched.
7. Existing six installer assets remain published; updater assets are additional release assets and release validation must no longer assume exactly six total assets after Goal 4.
8. Preserve the old repository update ZIP trust-boundary workflow separately; it must not become the desktop updater's execution path.

**Verification:** Static release contract plus synthetic manifest-generation tests using fake signatures/URLs. No real signing secret is needed in PR CI.

## Task 5 — Security and no-background-network regression

**Files:**
- Extend: `tests/test_update_trust_boundary.py`
- Create/modify: `tests/test_goal4_desktop_updater_contract.py`

**Checks:**
- No private key material or placeholder private key is committed.
- Only HTTPS GitHub Releases endpoint is permitted by Goal 4 configuration.
- Update install must be version-bound to the version shown to the user.
- Release notes are treated as text.
- No check/download/install is called from startup/setup/page load/timers.
- Web/PWA runtime cannot reach Tauri updater commands.
- Existing repository-package updater trust-boundary tests remain green.

## Task 6 — Goal 4 pre-packaging checkpoint

**Files:**
- Update PR #132 checkpoint/comment; do not edit product files solely to record status.
- Refresh integrity metadata only when Goal 4 runtime changes require it.

**Gate:**
- Goal 4 contracts green.
- Tauri `cargo check` green on Windows/macOS/Linux CI.
- Desktop-only UI behavior green.
- Release/updater metadata contract green.
- Existing repository updater trust-boundary regression green.
- No installed E2E claim yet.

Declare only: **Goal 4 IMPLEMENTATION COMPLETE — PRE-PACKAGING VERIFIED**.

## Task 7 — Return to Goal 3, then installed updater E2E

After Task 6, resume Goal 3 from the preserved work plus Goal 4 commits. Finish MSI/AppImage/macOS package inspection. Then perform the real updater test:

1. Build/install an older signed InkDOS desktop version.
2. Publish or use a controlled signed newer test release with valid `latest.json`.
3. Confirm no network update request occurs before the user clicks `Check for updates`.
4. Click `Check for updates`; verify current/latest/release notes.
5. Cancel once; verify no install occurs.
6. Check again and explicitly install.
7. Verify signature enforcement and successful transition to the newer version.
8. Verify tampered metadata/signature/artifact fails closed.
9. Verify Windows/macOS/Linux behavior as supported by package runners/manual installed test surfaces.

Only after this gate may Goal 4 be declared **END-TO-END VERIFIED**.

## Task 8 — Final InkDOS 2.3 closeout

Refresh integrity metadata, run the complete release validation/browser matrices/native package gates, merge/integrate according to the approved release process, tag the final 2.3 release, and verify published installers plus updater metadata correspond to the same release commit.