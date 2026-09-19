# Release Pipeline Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce InkDOS release plumbing to one tag-triggered release workflow, one validation-only desktop workflow, and only the supported installer/updater formats while preserving application behavior and the existing v2.3.0 public baseline.

**Architecture:** Release publication is driven only by an immutable `vX.Y.Z` tag. `.github/workflows/release.yml` owns validation, signed native builds, provenance, manifest generation, and publication; `.github/workflows/desktop-tauri.yml` owns non-release desktop contracts only. Redundant promotion state, duplicate native builds, and unsupported package formats are removed.

**Tech Stack:** GitHub Actions, Python contract tests, Rust 1.98.1, Tauri CLI 2.11.4, Tauri v2.

**Spec:** Approved in chat on 2026-09-17.

## Global Constraints

- Do not create or push a release tag during this work.
- Do not publish or make public a 2.4 release during this work.
- Preserve application functionality and data-integrity behavior.
- Keep only NSIS/EXE on Windows, DMG plus Tauri updater artifact on macOS, and AppImage on Linux.
- Release workflow must be tag-only; no `workflow_dispatch`, no `reuse_run_id`, no external promotion-state file.
- Provenance must describe artifacts produced by the same release workflow run.
- Pin the Rust toolchain and Tauri CLI to the versions proven by the last successful native build: Rust 1.98.1 and Tauri CLI 2.11.4.

---

### Task 1: Encode the simplified release contract

**Files:**
- Modify: `tests/test_tauri_desktop_contract.py`

- [ ] Update release-workflow assertions to require tag-only triggering, no manual/reuse path, reduced bundles, current-run provenance, and pinned Rust/Tauri CLI.
- [ ] Update desktop-workflow assertions to require validation-only behavior with no native build matrix.
- [ ] Update Tauri bundle-target assertions to require only `nsis`, `app`, `dmg`, and `appimage` and reject `msi`, `deb`, and `rpm`.
- [ ] Verify the updated contract fails against the existing implementation for the intended reasons.

### Task 2: Simplify workflows and packaging

**Files:**
- Delete: `.github/workflows/promote-release-tag.yml`
- Delete: `.github/release-promotion.json`
- Modify: `.github/workflows/release.yml`
- Modify: `.github/workflows/desktop-tauri.yml`
- Modify: `desktop/src-tauri/tauri.conf.json`
- Modify: `desktop/src-tauri/Cargo.toml`

- [ ] Make `release.yml` tag-only and remove all reuse/manual recovery branches.
- [ ] Reduce release bundles and validation to EXE, DMG, AppImage and their updater signature/archive artifacts.
- [ ] Keep provenance generated and consumed only from the current run.
- [ ] Remove native builds from `desktop-tauri.yml`; retain metadata, desktop contract, and staging checks.
- [ ] Remove WiX/MSI, DEB, and RPM package configuration.
- [ ] Pin Rust 1.98.1 and Tauri CLI 2.11.4 in release workflow; pin direct Tauri dependencies to versions observed in the successful build logs.
- [ ] Re-run the contract and repository validation checks.

### Task 3: Remove stale runtime/docs references

**Files:**
- Modify: `desktop/scripts/stage_web.py`
- Modify: `index.html`
- Modify: `README.md`
- Modify: `docs/UPDATE_MODEL.md`

- [ ] Stop staging `PROJECT_STATUS.md` as a desktop runtime document.
- [ ] Remove dead Status/Contribute footer links while preserving the maintained limitations/source links.
- [ ] Document the single tag-driven workflow and validation-only desktop workflow.
- [ ] Document the reduced installer set.
- [ ] Run contract/privacy/release validation after documentation changes.

### Task 4: Review, verify, and integrate

- [ ] Open a PR from `ci/simplify-release-pipeline` to `main`.
- [ ] Inspect the complete diff and any review/check feedback.
- [ ] Verify no tag or public release was created.
- [ ] If all available checks are green and no unresolved feedback remains, squash-merge the PR and verify `main` afterward.
