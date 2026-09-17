# Project status

Release: **InkDOS 2.4.0**

Status: **2.4 stable release promotion in progress; repository and merge-gate validation are green, and publication must still complete the signed cross-platform release workflow before the release is considered published**.

InkDOS contains six installed, physically independent workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB Reader and PDF Workspace. The functional roadmap remains preserved; current work is release validation, packaging and evidence-driven correction rather than broad feature construction.

## Current release line

InkDOS 2.4.0 promotes the completed 2.4 interface/localization layer and the hardened CI/release process to the stable line. English remains the native source interface. Optional locale packages provide Portuguese, Spanish, German, French, Simplified Chinese, Japanese and Russian presentation text without changing editor/runtime logic, file-format structures, formulas, serialization keys or user content.

Each workspace exposes compact Appearance / Interface / Language / Help controls while retaining app-local behavior and physical workspace independence. The 2.4 regression set also covers the first-open pointer/touch interception issue across all six workspaces.

The active release identity is defined by `VERSION.json`; generated build/source/release manifests are expected to match it. Historical freeze records remain historical evidence and are intentionally not rewritten to 2.4.0.

## Release pipeline

The release path now uses the same complete read-only integrity gate on pull requests and `main`, validates the merge candidate before integration, separates CI from manual update-package application, performs signing preflight, records immutable build provenance and can reuse already validated build artifacts for publish-only recovery.

The unified release workflow requires the release tag to belong to `main`, requires tag/version/Tauri metadata to agree, runs repository and updater contracts, builds signed Windows/macOS/Linux artifacts, verifies provenance and required artifact cardinality, builds `latest.json`, and publishes only after those stages succeed.

## Automated validation

The release gate covers repository structure and source locks, standalone workspace isolation, deterministic assets, localization/settings contracts, security/configuration contracts, preserved format round trips, browser regressions in Chromium, Firefox and WebKit, updater contracts, and native desktop packaging/integration checks.

A green synthetic matrix is necessary but not sufficient for host-specific acceptance. Playwright WebKit cannot fully prove behavior of every embedded iPad browser/container, system Share Sheet, native file-picker fallback or WebKit host policy. Real-device acceptance remains distinct from automated validation, and real-device observations remain authoritative when a host-specific issue cannot be reproduced synthetically.

## 2.4 release scope

The current line includes regression-backed work for:

- optional UI-only localization packages with English fallback;
- compact app-local Appearance / Interface / Language / Help controls;
- preservation of functional attributes, parser tokens, formulas, serialization keys and user content during localization;
- first-open pointer/touch interception regression coverage across all six workspaces;
- app-local density/language preference behavior and approved presentation-layer shared runtime;
- pre-merge integrity validation on the actual PR merge candidate;
- centralized shared-runtime policy consumed by repository validators;
- separated read-only CI and manual update-package workflows;
- release signing preflight, immutable provenance and publish-only artifact reuse;
- path-aware native desktop and stability workflows without weakening the universal integrity gate.

## Architecture and local-first boundary

Each workspace remains rooted under `apps/<workspace>/` and retains app-local runtime, state and I/O responsibilities. Home is an optional suite bridge, not a runtime dependency. The root service worker supplies the validated offline shell under HTTP(S).

InkDOS requires no application backend, telemetry service or remote document-processing service. File parsing, editing and export occur client-side. The desktop updater is the narrowly scoped exception for explicit user-requested release checking/install delivery and does not create an application backend.

## Format boundary

InkDOS targets practical local productivity rather than exhaustive parity with Microsoft Office, LibreOffice, Adobe Acrobat or every structure permitted by DOC/DOCX/RTF, XLS/XLSX, PPT/PPTX, EPUB and PDF specifications. Supported input does not imply that every imported construct is editable or round-tripped without loss.

The exact current limitations are maintained in `docs/KNOWN_LIMITATIONS.md`.

## Control-state note

`DEVELOPMENT_STATE.json` is the transactional updater's sequence ledger, not the public release number. Its `appliedSequence` and `currentPackage` identify the last accepted update package and should not be rewritten merely to make them resemble `VERSION.json`.

`FUNCTIONAL_STATE.json` and `STABILITY_STATE.json` remain lifecycle/control records for the completed roadmap and freeze program. The human-facing current stage is this document: **2.4.0 stable release promotion and publication**.
