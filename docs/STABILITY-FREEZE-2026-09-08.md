# Stability Functional Isolation Freeze — 2026-09-08

Status: **FREEZE CANDIDATE**

Program: `stability-functional-isolation`
Working branch: `audit/stability-functional-isolation`
Runtime anchor under freeze validation: `9da9b798c624e3db6bcf933d85ed19892997bf5f`

## Scope

This freeze records the regression/stability baseline required by the blocking stability directives. It does not add a user-facing feature, expand file-format fidelity, or authorize PPT-P2/XLS-S1/XLS-S2 work before the freeze gate completes.

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

The six workspace stability audits completed before this freeze candidate. Their regression gates cover command/control independence, relevant history/state behavior, representative open/save/reopen paths where applicable, clean boot, and Chromium/Firefox/WebKit support to the defined level.

The integrated cross-suite run `34270011352` passed:

- static shell/precache contract;
- Chromium online and server-removed offline bootstrap across all six workspaces;
- Firefox online and server-removed offline bootstrap across all six workspaces;
- WebKit online and server-removed offline bootstrap across all six workspaces.

The stability program also discovered and fixed objective regressions, including Spreadsheets Undo/Redo state projection, and converted discovered failures into automated regression coverage.

## Freeze gate

The repository is not considered frozen merely because this document exists. `.github/workflows/stability-freeze-regression.yml` must pass on the freeze-candidate commit. The gate aggregates the six workspace stability contracts, cross-suite contract, security configuration regression, architecture/suite contract validation, and the complete primary browser stability matrix.

Only after that gate is green may `STABILITY_STATE.json` transition to `active: false` and this document transition from **FREEZE CANDIDATE** to **FROZEN**.

## Post-freeze rule

After the final freeze, later feature development must run the feature's own tests plus the frozen workspace regression gate and cross-suite bootstrap/offline/isolation gate. A new feature is not approved solely because its own happy path works.
