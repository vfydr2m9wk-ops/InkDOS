# Stability Functional Isolation Refreeze — 2026-09-10

Status: **FREEZE CANDIDATE**

Program: `stability-functional-isolation`
Working branch: `audit/stability-functional-isolation`
Runtime anchor under freeze validation: `44896f583d14dba6ba00b4ee1311f85ed513ad8a`
Cross-suite remediation revalidation run: `34457839525`

## Scope

This refreeze candidate supersedes the 2026-09-08 runtime freeze only as the active runtime baseline. The earlier freeze document remains historical evidence. The new candidate incorporates the subsequently approved functional roadmap through PPT-P2, XLS-S1, XLS-S2 and final Audit, plus the real-device remediation merged as PR #58.

The remediation addresses the observed PDF kinetic-scroll instability, Presentation fidelity and legacy-PPT conversion gaps, TXT large-file stalls, EPUB selection annotation UX gaps, and Spreadsheet color fidelity loss. It does not claim exhaustive compatibility with unsupported file-format features.

The audited workspaces remain:

1. PDF Workspace
2. Documents
3. Presentations
4. Plain Text
5. EPUB Reader
6. Spreadsheets

The final integration layer is the cross-suite frame/bootstrap/offline/service-worker gate.

## Required architectural baseline

The refreeze preserves these rules:

- a button is a command binding, not the feature implementation;
- semantic commands remain callable independently of their visual controls where technically applicable;
- frame/toolbar layout does not own editor or format semantics;
- viewport/rendering, session/history/state, and persistence/import/export retain app-local ownership boundaries;
- no feature may depend on toolbar DOM order or unrelated sibling controls;
- functional modularity remains proportional: split by responsibility, not by button count or arbitrary file-size targets;
- all six workspaces remain physically independent under `apps/<workspace>/`;
- the root service worker must preserve standalone/offline availability for every workspace.

## Evidence entering refreeze

PR #58 was validated at head `890ce359edc65632dc9b2a06031a2b876481abad` and squash-merged to the runtime anchor `44896f583d14dba6ba00b4ee1311f85ed513ad8a`.

The fresh PR gate set completed successfully for integrity/update, PDF, Documents, Presentations, Plain Text, EPUB and Spreadsheets stability regressions, PPT-P1 round-trip, PPT-P2, XLS-S1, XLS-S2, the pre-phase architecture audit, the cross-suite stability regression and the aggregate stability-freeze regression. Cross-suite workflow run `34457839525` is the revalidation evidence recorded in `STABILITY_STATE.json`.

The format-preservation policy remains conservative: unsupported OOXML/package content is preserved where the existing package-preserving contracts support it, while legacy or unsupported editable semantics are not silently claimed as fully supported.

## Freeze gate

The repository is not considered refrozen merely because this candidate exists. `.github/workflows/stability-freeze-regression.yml` must pass on the freeze-candidate checkpoint, including suite architecture/offline validation, all frozen static contracts, PDF.js security configuration, preserved format round-trips, and the primary stability browser matrix in Chromium, Firefox and WebKit.

Only after that candidate gate is green may `STABILITY_STATE.json` transition to `active: false`, this document transition to **FROZEN**, and the candidate record receive its `freezeGateCommit` and `freezeGateRun` evidence.

The final metadata-only frozen checkpoint must itself remain green under the same aggregate gate. A red final run invalidates closure until explained and corrected.

## Post-freeze rule

The domestic-use roadmap is at its final Freeze phase. Future bug fixes or user-test remediations must preserve the frozen stability contracts and should not broaden format-fidelity claims without new regression evidence.
