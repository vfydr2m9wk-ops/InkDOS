# Unified Web and Desktop Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `main` the single release source for InkDOS web/PWA and Tauri desktop packages, with one `vX.Y.Z` tag producing one GitHub Release containing Windows, macOS, and Linux installers from the same commit.

**Architecture:** Keep the existing root web/PWA tree authoritative. Keep Tauri under `desktop/` as a packaging/host layer. Add a tag/version validation utility plus a unified GitHub Actions workflow that validates, builds on native runners, and publishes only after all platform builds succeed.

**Tech Stack:** HTML/CSS/vanilla JavaScript, Python 3.11 release utilities/tests, Rust/Tauri v2, GitHub Actions, GitHub Releases.

**Spec:** `docs/superpowers/specs/2026-09-12-unified-web-desktop-release-design.md`

## Global Constraints

- `main` remains the canonical source branch.
- `VERSION.json` is the product version source.
- Release tags use exact `vX.Y.Z` form and must match `VERSION.json.version`.
- Windows, macOS, Linux, and web must correspond to the same tagged commit.
- Generated installers must never be committed to Git.
- Existing browser/PWA behavior and workspace ownership boundaries must remain intact.
- Production signing/notarization is not introduced without credentials.

---

### Task 1: Release contract and version utility

**Files:**
- Modify: `tests/test_tauri_desktop_contract.py`
- Create: `desktop/scripts/release_version.py`

**Interfaces:**
- Consumes: repository `VERSION.json`, optional tag string, `desktop/src-tauri/tauri.conf.json`.
- Produces: CLI commands `--check-config`, `--sync-config`, and `--check-tag TAG`; exit non-zero on mismatch.

- [ ] **Step 1: Write failing contract checks**

Extend `tests/test_tauri_desktop_contract.py` to require `desktop/scripts/release_version.py`, require release workflow markers, require tag/version validation, and remove the hard-coded assertion that the release must always equal `2.1.0`.

- [ ] **Step 2: Run the desktop contract and verify RED**

Run: `python tests/test_tauri_desktop_contract.py`
Expected: FAIL because `desktop/scripts/release_version.py` and the unified release workflow do not exist yet.

- [ ] **Step 3: Implement the release version utility**

The utility must read `VERSION.json`, validate semantic version `X.Y.Z`, compare `vX.Y.Z` tag values, and either verify or synchronize `tauri.conf.json.version`. It must not change `VERSION.json`.

- [ ] **Step 4: Run focused utility checks**

Run:
`python desktop/scripts/release_version.py --check-config`
`python desktop/scripts/release_version.py --check-tag v2.1.0`
Expected: both succeed on the current branch.

- [ ] **Step 5: Commit**

Commit message: `feat: add unified release version contract`

### Task 2: Unified CI and tag release workflow

**Files:**
- Modify: `.github/workflows/desktop-tauri.yml`
- Create: `.github/workflows/release.yml`
- Modify: `tests/test_tauri_desktop_contract.py`

**Interfaces:**
- Consumes: Task 1 `release_version.py` CLI.
- Produces: branch validation on `main`/`desktop-tauri`; tag release on `v*.*.*`; native build artifacts; one GitHub Release.

- [ ] **Step 1: Add failing workflow assertions**

Require the branch workflow to validate `main` as well as `desktop-tauri`. Require the release workflow to trigger on `v*.*.*`, use `contents: write` only where publication requires it, call `--check-tag`, wait for Windows/macOS/Linux build jobs, download all artifacts, and publish them into one release.

- [ ] **Step 2: Run contract and verify RED**

Run: `python tests/test_tauri_desktop_contract.py`
Expected: FAIL because the release workflow is missing.

- [ ] **Step 3: Update desktop validation workflow**

Make `.github/workflows/desktop-tauri.yml` run on pushes to `main` and `desktop-tauri`, keep `workflow_dispatch`, retain read-only permissions, and add version-config validation before builds.

- [ ] **Step 4: Add `.github/workflows/release.yml`**

The workflow must validate the tag against `VERSION.json`, run desktop contracts/staging, build platform bundles on native runners, upload each platform bundle as an artifact, then use a final Linux release job with `contents: write` to download all artifacts and publish them with `gh release create "$GITHUB_REF_NAME" ...` only after all builds succeed. Release notes must include `https://vfydr2m9wk-ops.github.io/InkDOS/`.

- [ ] **Step 5: Run contract and staging checks**

Run:
`python tests/test_tauri_desktop_contract.py`
`python desktop/scripts/stage_web.py --check`
Expected: PASS.

- [ ] **Step 6: Commit**

Commit message: `feat: publish unified tagged desktop releases`

### Task 3: Repository hygiene and documentation

**Files:**
- Modify: `.gitignore`
- Modify: `docs/superpowers/specs/2026-09-12-tauri-desktop-distribution-design.md`

**Interfaces:**
- Consumes: unified release model.
- Produces: explicit binary/build-output exclusions and updated distribution documentation.

- [ ] **Step 1: Add failing hygiene assertions**

Require `.gitignore` to exclude `desktop/web-dist/`, `desktop/src-tauri/target/`, `*.dmg`, `*.AppImage`, `*.msi`, `*.rpm`, and installer `.exe` outputs without blocking source executables elsewhere.

- [ ] **Step 2: Run contract and verify RED**

Run: `python tests/test_tauri_desktop_contract.py`
Expected: FAIL on missing desktop build-output ignores.

- [ ] **Step 3: Add narrow build-output ignores and update design**

Ignore only generated desktop distribution paths/extensions needed by this build. Update the older desktop distribution spec to point to the unified tag/release design for production publishing.

- [ ] **Step 4: Run contract again**

Run: `python tests/test_tauri_desktop_contract.py`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `docs: align desktop packaging with unified releases`

### Task 4: Branch verification and integration

**Files:**
- No new production files; integration task.

**Interfaces:**
- Consumes: completed `desktop-tauri` branch.
- Produces: reviewed/merged `main` commit containing web + desktop infrastructure.

- [ ] **Step 1: Run fresh verification on branch**

Verify GitHub Actions `InkDOS Tauri desktop` is green at the branch head. Verify the desktop contract and native Windows/macOS/Linux build jobs complete successfully.

- [ ] **Step 2: Compare against `main`**

Confirm changes are additive to desktop/release infrastructure and intended docs/tests; verify no workspace engine was removed.

- [ ] **Step 3: Open PR `desktop-tauri` -> `main`**

PR title: `feat: unify InkDOS web and desktop distribution`

- [ ] **Step 4: Merge only after green checks**

Use an ordinary merge commit so the feature branch history remains auditable. Verify the merged `main` head contains `desktop/src-tauri/` and both validation/release workflows.

### Task 5: Publish the first unified version tag

**Files:**
- No repository source changes unless a version collision is found.

**Interfaces:**
- Consumes: merged `main` SHA, `VERSION.json.version`.
- Produces: `v2.1.0` and GitHub Release `InkDOS 2.1.0` when that tag is still unused.

- [ ] **Step 1: Recheck tag availability**

Fetch `refs/tags/v2.1.0`. Expected before creation: 404/not found.

- [ ] **Step 2: Create the tag from merged `main`**

Use the available GitHub release/tag mechanism without moving any pre-existing tag. Target the merged `main` SHA.

- [ ] **Step 3: Verify tag-triggered workflow**

Confirm tag/version validation passes, all native build jobs pass, and release publication runs only after all builds.

- [ ] **Step 4: Verify release assets**

Confirm the GitHub Release contains Windows `.exe` and `.msi`, macOS `.dmg`, Linux `.deb`, `.AppImage`, and `.rpm`, plus GitHub source archives, all associated with `v2.1.0`.

- [ ] **Step 5: Verify web referent**

Confirm release notes link to the canonical web edition and the tag points to the same source commit represented by the desktop packages.
