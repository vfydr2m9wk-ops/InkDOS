# Project status

Release: **InkDOS 2.0.12**

Six installed independent workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB Reader and PDF Workspace. InkDOS 2.0.12 preserves the existing appearance, empty-workspace, Share, single-delivery Save and PDF frame contracts while making standalone app extraction an explicit validated property.

## Stability baseline

The blocking `stability-functional-isolation` program completed its six-workspace audit plus the integrated cross-suite frame/bootstrap/offline audit on 2026-09-08. The frozen baseline is recorded in `docs/STABILITY-FREEZE-2026-09-08.md` and enforced by `.github/workflows/stability-freeze-regression.yml`.

The aggregate freeze candidate passed suite architecture/offline validation, all frozen static contracts, the PDF.js security configuration regression, preserved format round-trips, and the complete primary stability browser suite in Chromium, Firefox and WebKit. The stability work does not change the 2.0.12 functional release scope or claim broader file-format fidelity.

## Standalone and suite integration

Each workspace remains physically rooted under its own `apps/<workspace>/` directory and retains its own runtime, state and I/O implementation. Home is now an optional bridge: the suite launcher adds `suite=1` to workspace navigation, and the corresponding app-local frame module exposes the Home action only in that integrated context. When opened directly or extracted, the workspace removes the Home target from its active frame without requiring a suite runtime.

The release gate now copies each workspace to an isolated temporary directory, verifies that its non-Home entry resources resolve within that app root, scans for cross-app runtime references, and checks that the offline service-worker shell contains no missing files. This directly covers the strict-standalone gap identified during the previous modularity audit.

## EPUB polish

EPUB previously had good logical separation but several core modules were physically flattened at the app root. Version 2.0.12 moves those existing responsibilities into app-private directories without intentionally changing algorithms:

- package reading and EPUB writing under `io/`;
- book model, content projection and annotation projection under `engine/`;
- annotation persistence under `state/`;
- rendering under `view/`;
- start-state presentation CSS under `ui/`.

`app.js` remains the composition layer, while `index.html` now loads the physically separated modules. The old flattened module copies are absent, and the release gate requires the new EPUB layout.

## Preserved contracts

Appearance remains horizontally synchronized through `inkdos2:appearance`, while every workspace retains its app-local appearance key and controller. Save and Share remain unavailable until a real active document/book/PDF exists according to each workspace's private state. The 2.0.11 one-Save/one-delivery rule remains active in Documents, Spreadsheets, Presentations, Plain Text and PDF.

The frozen stability baseline additionally requires that semantic commands remain independent of their visual controls where applicable, frame/toolbar layout not own editor semantics, app-local responsibility boundaries remain intact, and all six workspaces continue to bootstrap through the root offline shell.

## Scope boundary

This release is code-structure polish. It does not claim broader DOCX/XLSX/PPTX/EPUB/PDF compatibility or LibreOffice-level fidelity. Format expansion remains a later per-workspace task and must preserve the same app-private parser/writer boundaries and the frozen stability gates.

PDF otherwise retains the user-accepted P4.2 functional baseline. See `PDF-CLOSURE-AUDIT.md` for its verification scope.
