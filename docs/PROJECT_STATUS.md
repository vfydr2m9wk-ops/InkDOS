# Project status

Release: **InkDOS 2.1.0**

Status: **post-hardening release; real-device acceptance in progress**.

InkDOS contains six installed, physically independent workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB Reader and PDF Workspace. The original domestic-use functional roadmap (TXT-T1/T2, EPUB-E1/E2, PDF-P1/P2, DOC-D1/D2, PPT-P1/P2, XLS-S1/S2 and the integrated Audit/Freeze program) is complete as a historical implementation baseline. Current work is no longer broad feature construction; it is acceptance testing and evidence-driven correction against real files and real host behavior.

## Current release line

InkDOS 2.1.0 consolidates the stability and compatibility work performed after the 2.0.12 structural release. The active release identity is defined by `VERSION.json`; generated build/source/release manifests are expected to match it.

The 2.0.12 freeze records remain historical evidence and are intentionally not rewritten to 2.1.0. In particular, `docs/STABILITY-FREEZE-2026-09-10.md`, the immutable regression anchors and earlier CI/run references continue to describe the state that actually existed when those records were created.

## Automated validation

The release gate covers repository structure and source locks, standalone workspace isolation, deterministic assets, security/configuration contracts, preserved format round trips, and browser regressions in Chromium, Firefox and WebKit.

A green synthetic matrix is necessary but not sufficient for host-specific acceptance. Playwright WebKit cannot fully prove behavior of an embedded iPad browser/container, system Share Sheet, native file-picker fallback or every WebKit host policy. Real iPad/XeOS observations therefore remain authoritative when a host-specific issue cannot be reproduced synthetically.

## Hardening incorporated into the 2.1.0 line

The current line includes regression-backed work for:

- suite-wide Save / Discard / Cancel protection on destructive navigation;
- confirmed-delivery gating so dirty state is not cleared merely because a Save request resolved without verified delivery;
- single-flight / single-delivery protection against overlapping Save attempts and duplicate host delivery paths;
- local legacy DOC import with editable DOCX promotion and no DOC write-back;
- legacy XLS import into the XLSX editing/export path;
- legacy PPT import, PPT-to-PPTX promotion and additional fidelity/clipping handling;
- persistent PDF and EPUB annotation workflows plus pending-draft protection;
- EPUB WebKit/ZIP compatibility hardening, including deflate fallback and additional package/path/content projection cases;
- authorized Home exits that avoid a second native `beforeunload` prompt after the user has already chosen Save or Discard inside InkDOS.

These statements describe code and regression coverage. They do not convert an unconfirmed device-specific symptom into a closed bug.

## Real-device acceptance priorities

The current hands-on acceptance cycle should concentrate on: one deliberate Save producing one intended output on iPad/XeOS; correct Save/Discard/Cancel behavior when leaving dirty work; EPUB opening/rendering with real user files; legacy PPT/PPTX visual fidelity and text clipping; PDF opening/annotation/export behavior in the host; and any remaining visual inconsistency on Home or inside a workspace.

A device issue is considered closed only after either the original symptom is reproduced and corrected with a regression, or the corrected build is confirmed on the affected real-device path.

## Architecture and local-first boundary

Each workspace remains rooted under `apps/<workspace>/` and retains app-local runtime, state and I/O responsibilities. Home is an optional suite bridge, not a runtime dependency. The root service worker supplies the validated offline shell under HTTP(S).

InkDOS requires no application backend, telemetry service or remote document-processing service. File parsing, editing and export occur client-side.

## Format boundary

InkDOS targets practical local productivity rather than exhaustive parity with Microsoft Office, LibreOffice, Adobe Acrobat or every structure permitted by DOC/DOCX/RTF, XLS/XLSX, PPT/PPTX, EPUB and PDF specifications. Supported input does not imply that every imported construct is editable or round-tripped without loss.

The exact current limitations are maintained in `docs/KNOWN_LIMITATIONS.md`.

## Control-state note

`DEVELOPMENT_STATE.json` is the transactional updater's sequence ledger, not the public release number. Its `appliedSequence` and `currentPackage` identify the last accepted update package and should not be rewritten merely to make them resemble `VERSION.json`.

`FUNCTIONAL_STATE.json` and `STABILITY_STATE.json` are lifecycle/control records for the completed roadmap and freeze program. The human-facing current stage is this document: **2.1.0 real-device acceptance and bug correction**.
