# Project status

Release: **InkDOS 2.3.0**

Status: **2.3 release candidate; web/PWA and native validation green through the pre-release packaging checkpoint; signed installed-updater end-to-end validation remains pending final signed release artifacts**.

InkDOS contains six installed, physically independent workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB Reader and PDF Workspace. The original domestic-use functional roadmap (TXT-T1/T2, EPUB-E1/E2, PDF-P1/P2, DOC-D1/D2, PPT-P1/P2, XLS-S1/S2 and the integrated Audit/Freeze program) is complete as a historical implementation baseline. Current work is release validation and evidence-driven correction rather than broad feature construction.

## Current release line

InkDOS 2.3.0 preserves the unified local-first web/PWA and Tauri desktop architecture while adding the completed 2.3 intervention work: CSV/TSV preservation, suite-wide adaptive interface density, Presentations corrections, PDF Open user-gesture correction, desktop packaging/integration work, and the manual-only desktop updater.

The active release identity is defined by `VERSION.json`; generated build/source/release manifests are expected to match it. Historical freeze records remain historical evidence and are intentionally not rewritten to 2.3.0.

The desktop updater is Tauri-only and is hidden/inert in web/PWA. It performs no startup checks, polling, telemetry or background update network activity. Update network access begins only after the user explicitly chooses Check for updates; installation remains a separate explicit action. The release path uses signed Tauri v2 updater artifacts and validates metadata, artifact and signature trust boundaries. Installed end-to-end updating against the finalized signed 2.3.0 release artifacts must not be considered complete until those artifacts exist and the installed path has actually been exercised.

## Automated validation

The release gate covers repository structure and source locks, standalone workspace isolation, deterministic assets, security/configuration contracts, preserved format round trips, browser regressions in Chromium, Firefox and WebKit, updater contracts, and native desktop packaging/integration checks.

A green synthetic matrix is necessary but not sufficient for host-specific acceptance. Playwright WebKit cannot fully prove behavior of an embedded iPad browser/container, system Share Sheet, native file-picker fallback or every WebKit host policy. Real-device acceptance remains distinct from automated validation, and real-device observations remain authoritative when a host-specific issue cannot be reproduced synthetically.

## 2.3 release-candidate scope

The current line includes regression-backed work for:

- preserved CSV/TSV delimiter and format behavior;
- suite-wide adaptive interface density;
- Presentations overflow and object-interaction corrections;
- PDF Open behavior that preserves the browser user gesture for the file picker;
- native Windows, macOS and Linux packaging/integration validation, including associations, launchers and multiwindow behavior;
- a manual-only desktop updater with no automatic/background update network path;
- suite-wide Save / Discard / Cancel protection on destructive navigation;
- confirmed-delivery gating so dirty state is not cleared merely because a Save request resolved without verified delivery;
- single-flight / single-delivery protection against overlapping Save attempts and duplicate host delivery paths;
- local legacy DOC/XLS/PPT import and promotion into their modern editable/export paths;
- persistent PDF and EPUB annotation workflows plus pending-draft protection;
- EPUB WebKit/ZIP compatibility hardening.

These statements describe code and regression coverage. They do not convert an unconfirmed device-specific symptom or the still-pending signed installed-updater E2E into a closed acceptance item.

## Remaining release gate

Before InkDOS 2.3.0 is declared complete, the coherent 2.3 snapshot must have refreshed integrity metadata and pass the final repository/cross-browser/cross-platform validation. The established release process must then produce the finalized signed native release artifacts, after which the real installed updater path must be exercised against those artifacts. A failure in that installed path is a release failure requiring correction and revalidation, not evidence to be waived.

## Architecture and local-first boundary

Each workspace remains rooted under `apps/<workspace>/` and retains app-local runtime, state and I/O responsibilities. Home is an optional suite bridge, not a runtime dependency. The root service worker supplies the validated offline shell under HTTP(S).

InkDOS requires no application backend, telemetry service or remote document-processing service. File parsing, editing and export occur client-side. The desktop updater is the narrowly scoped exception for explicit user-requested release checking/install delivery and does not create an application backend.

## Format boundary

InkDOS targets practical local productivity rather than exhaustive parity with Microsoft Office, LibreOffice, Adobe Acrobat or every structure permitted by DOC/DOCX/RTF, XLS/XLSX, PPT/PPTX, EPUB and PDF specifications. Supported input does not imply that every imported construct is editable or round-tripped without loss.

The exact current limitations are maintained in `docs/KNOWN_LIMITATIONS.md`.

## Control-state note

`DEVELOPMENT_STATE.json` is the transactional updater's sequence ledger, not the public release number. Its `appliedSequence` and `currentPackage` identify the last accepted update package and should not be rewritten merely to make them resemble `VERSION.json`.

`FUNCTIONAL_STATE.json` and `STABILITY_STATE.json` are lifecycle/control records for the completed roadmap and freeze program. The human-facing current stage is this document: **2.3.0 release-candidate validation and release closure**.
