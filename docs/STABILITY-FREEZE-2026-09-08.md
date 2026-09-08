# Stability Functional Isolation Freeze — 2026-09-08

Status: **FROZEN**

Program: `stability-functional-isolation`
Working branch: `audit/stability-functional-isolation`
Runtime anchor: `9da9b798c624e3db6bcf933d85ed19892997bf5f`
Freeze-gate commit: `f17e102e3e9b612e86da020ba3ab880b16f5741c`
Freeze-gate run: `34270610710`

## Scope

This freeze records the regression/stability baseline required by the blocking stability directives. It does not add a user-facing feature, expand file-format fidelity, or change the InkDOS 2.0.12 functional release scope.

The audited workspaces are:

1. PDF Workspace
2. Documents
3. Presentations
4. Plain Text
5. EPUB Reader
6. Spreadsheets

The final integration layer is the cross-suite frame/bootstrap/offline/service-worker gate.

## Required architectural baseline

The frozen baseline preserves these rules:

- a button is a command binding, not the feature implementation;
- semantic commands remain callable independently of their visual controls where technically applicable;
- frame/toolbar layout does not own editor or format semantics;
- viewport/rendering, session/history/state, and persistence/import/export retain app-local ownership boundaries;
- no feature may depend on toolbar DOM order or unrelated sibling controls;
- functional modularity is proportional: split by responsibility, not by file size or by individual button/action;
- all six workspaces remain physically independent under `apps/<workspace>/` and boot without a shared runtime dependency;
- the root service worker must preserve standalone/offline availability for every workspace.

## Evidence entering freeze

The six workspace stability audits completed before this freeze. Their regression gates cover command/control independence, relevant history/state behavior, representative open/save/reopen paths where applicable, clean boot, and Chromium/Firefox/WebKit support to the defined level.

The integrated cross-suite run `34270011352` passed:

- static shell/precache contract;
- Chromium online and server-removed offline bootstrap across all six workspaces;
- Firefox online and server-removed offline bootstrap across all six workspaces;
- WebKit online and server-removed offline bootstrap across all six workspaces.

The stability program also discovered and fixed objective regressions, including Spreadsheets Undo/Redo state projection, and converted discovered failures into automated regression coverage.

## Freeze gate

The aggregate freeze gate at commit `f17e102e3e9b612e86da020ba3ab880b16f5741c`, workflow run `34270610710`, passed all required jobs:

- suite architecture and offline contract validation;
- all frozen static workspace/cross-suite contracts;
- PDF.js security configuration regression;
- complete primary stability browser suite in Chromium;
- complete primary stability browser suite in Firefox;
- complete primary stability browser suite in WebKit;
- all preserved `*roundtrip.py` format/persistence regressions in Chromium.

`STABILITY_STATE.json` therefore records the stability program as inactive and frozen. The final metadata-only freeze commit must itself remain green under the same `stability-freeze-regression.yml` workflow; a future red run invalidates the frozen status until explained and corrected.

## Post-freeze rule

Later feature development must run the feature's own tests plus the applicable frozen workspace regression gate and the cross-suite bootstrap/offline/isolation gate. A feature is not approved solely because its own happy path works.

The previously recorded roadmap may resume only under a subsequent authorized development phase. This freeze does not itself advance PPT-P2, XLS-S1 or XLS-S2.
