# InkDOS Tauri Desktop Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an installable Tauri v2 edition of InkDOS on an isolated `desktop-tauri` branch while preserving the browser/PWA product and generating native Windows, macOS and Linux installers in GitHub Actions.

**Architecture:** Keep the existing InkDOS HTML/CSS/JavaScript source unchanged. A Python staging step copies only web-runtime assets into `desktop/web-dist`, injects a desktop host bridge into staged HTML, and Tauri packages that staged directory. The bridge maps file-save behavior to Tauri native dialog/filesystem APIs, maps file-input opening to Tauri native dialogs when possible with a safe WebView fallback, and routes external links to the OS browser.

**Tech Stack:** Tauri v2, Rust, `tauri-plugin-dialog`, `tauri-plugin-fs`, `tauri-plugin-opener`, vanilla JavaScript, Python 3.11 contract/staging tests, GitHub Actions native runners.

**Spec:** `docs/superpowers/specs/2026-09-12-tauri-desktop-distribution-design.md`

## Global Constraints

- Do not modify or force-update `main`.
- Desktop application name: `InkDOS`.
- Desktop application version: `2.1.0`, matching `VERSION.json`.
- Bundle identifier: `com.inkdos.desktop`.
- Tauri major version: v2.
- No Electron and no bundled Node.js runtime.
- Existing workspace parsers, writers, editors and state machines remain JavaScript-owned.
- Browser/PWA runtime source remains unchanged; desktop-specific injection happens only in staged build output.
- Files selected by native dialogs are dynamically scoped; do not grant arbitrary filesystem scopes.
- Unsigned branch artifacts are acceptable; production signing/notarization is out of scope.

---

### Task 1: Desktop Contract Tests and CI Skeleton

**Files:**
- Create: `tests/test_tauri_desktop_contract.py`
- Create: `.github/workflows/desktop-tauri.yml`

**Interfaces:**
- Consumes: repository layout and `VERSION.json`.
- Produces: static assertions for desktop config, staging, least-privilege permissions, and native build matrix.

- [ ] Write contract tests requiring Tauri v2 config, `com.inkdos.desktop`, staged `frontendDist`, dialog/fs/opener plugins, no Electron/Node runtime, Windows/macOS/Linux targets, and desktop-host bridge markers.
- [ ] Add a branch-only GitHub Actions workflow that runs the contract test before native build jobs.
- [ ] Push the test before implementation and verify the contract job fails because desktop files do not exist yet.

### Task 2: Static Asset Staging and Desktop Host Bridge

**Files:**
- Create: `desktop/scripts/stage_web.py`
- Create: `desktop/desktop-host.js`
- Create: `desktop/.gitignore`

**Interfaces:**
- Consumes: repository root `index.html`, `service-worker.js`, `manifest.webmanifest`, `assets/`, `apps/`, and runtime metadata needed by pages.
- Produces: `desktop/web-dist/` with staged InkDOS assets and injected `/desktop-host.js` references.

- [ ] Stage only runtime files/directories; exclude `.git`, `desktop`, tests, docs, CI and release-only metadata not required by pages.
- [ ] Inject the desktop bridge immediately after `<head>` in each staged HTML file without editing source HTML.
- [ ] In the bridge, expose desktop capability metadata; provide a `showSaveFilePicker` compatibility adapter backed by `window.__TAURI__.dialog.save` + `window.__TAURI__.fs.writeFile`; intercept file-input clicks using `dialog.open` + `fs.readFile` when DataTransfer is available, falling back to the native WebView picker otherwise; route external HTTP(S) links through `window.__TAURI__.opener.openUrl`.
- [ ] Preserve browser semantics by limiting the bridge to staged desktop assets.
- [ ] Run the staging contract locally in CI and validate every staged HTML file contains exactly one bridge injection.

### Task 3: Tauri v2 Shell and Least-Privilege Capabilities

**Files:**
- Create: `desktop/src-tauri/Cargo.toml`
- Create: `desktop/src-tauri/build.rs`
- Create: `desktop/src-tauri/src/main.rs`
- Create: `desktop/src-tauri/tauri.conf.json`
- Create: `desktop/src-tauri/capabilities/default.json`

**Interfaces:**
- Consumes: `desktop/web-dist`.
- Produces: a Tauri application loading `index.html` as window `main`.

- [ ] Configure `frontendDist` to `../web-dist` and `withGlobalTauri=true`.
- [ ] Initialize only dialog, filesystem and opener plugins.
- [ ] Grant `core:default`, `dialog:allow-open`, `dialog:allow-save`, `fs:allow-read-file`, `fs:allow-write-file`, and `opener:allow-default-urls`; do not add a broad static filesystem scope.
- [ ] Configure a standard resizable desktop window and bundle targets per platform.
- [ ] Configure current-user NSIS installation on Windows and WebView2 bootstrapper behavior.
- [ ] Validate JSON/TOML syntax and `cargo check` on native CI runners.

### Task 4: Native Packaging Matrix

**Files:**
- Modify: `.github/workflows/desktop-tauri.yml`
- Create: `desktop/README.md`

**Interfaces:**
- Consumes: staged web assets and Tauri shell.
- Produces: uploaded workflow artifacts containing Windows `.exe`/`.msi`, macOS `.dmg`/`.app`, and Linux `.deb`/`.AppImage`/`.rpm` when produced by Tauri.

- [ ] Build on `windows-latest`, `macos-latest`, and `ubuntu-22.04`.
- [ ] Install Rust stable and Tauri CLI from Cargo only; do not install Node for the desktop build.
- [ ] Install official Tauri Linux prerequisites including WebKitGTK 4.1.
- [ ] Run `stage_web.py`, generate platform icons from the existing InkDOS PNG, and invoke `cargo tauri build` with native bundle targets.
- [ ] Upload bundle directories as `InkDOS-Windows`, `InkDOS-macOS`, and `InkDOS-Linux` artifacts.
- [ ] Document local build commands, unsigned-artifact limitations, expected output paths and artifact names.

### Task 5: Verification and Branch Completion

**Files:**
- Verify only; no required source files.

**Interfaces:**
- Consumes: completed branch.
- Produces: evidence that source web behavior is preserved and platform artifacts build.

- [ ] Run `python tests/test_tauri_desktop_contract.py`.
- [ ] Run existing static contract suite in the desktop workflow.
- [ ] Run `python desktop/scripts/stage_web.py --check` and verify deterministic staging.
- [ ] Run `cargo check` on the Tauri shell.
- [ ] Confirm all three native build jobs complete and inspect uploaded artifact filenames.
- [ ] Compare `main...desktop-tauri` and verify all functional changes are isolated to the branch and no source workspace engine was duplicated or rewritten.
