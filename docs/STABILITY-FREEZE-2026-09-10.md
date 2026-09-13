# Stability Functional Isolation Refreeze — 2026-09-10

Status: **FROZEN**

Program: `stability-functional-isolation`
Working branch used for validation: `audit/stability-functional-isolation`
Frozen runtime anchor: `44896f583d14dba6ba00b4ee1311f85ed513ad8a`
Cross-suite remediation revalidation run: `34457839525`
Freeze candidate gate commit: `7e852032e21a35710e4fcb3a0c33d0f76ff609e6`
Freeze candidate aggregate gate run: `34458997715`

## Scope

This refreeze supersedes the 2026-09-08 runtime freeze as the active domestic-use stability baseline. The earlier freeze document remains historical evidence. The 2026-09-10 baseline includes the completed functional roadmap through PPT-P2, XLS-S1, XLS-S2 and Audit, plus the real-device remediation merged as PR #58.

The remediation covers the observed PDF kinetic-scroll instability, Presentation fidelity and legacy-PPT conversion gaps, TXT large-file stalls, EPUB selection annotation UX gaps, and Spreadsheet color fidelity loss. It does not claim exhaustive compatibility with unsupported file-format features.

The audited workspaces are PDF Workspace, Documents, Presentations, Plain Text, EPUB Reader and Spreadsheets, followed by the integrated cross-suite frame/bootstrap/offline gate.

## Architectural baseline

The freeze preserves these rules:

- a button is a command binding, not the feature implementation;
- semantic commands remain callable independently of their visual controls where technically applicable;
- frame/toolbar layout does not own editor or format semantics;
- viewport/rendering, session/history/state, and persistence/import/export retain app-local ownership boundaries;
- no feature may depend on toolbar DOM order or unrelated sibling controls;
- functional modularity remains proportional: split by responsibility, not by button count or arbitrary file-size targets;
- all six workspaces remain physically independent under `apps/<workspace>/`;
- the root service worker preserves standalone/offline availability for every workspace.

## Validation evidence

PR #58 was validated at head `890ce359edc65632dc9b2a06031a2b876481abad` and squash-merged to runtime anchor `44896f583d14dba6ba00b4ee1311f85ed513ad8a`.

The remediation checkpoint passed the applicable integrity/update, workspace stability, PPT-P1 round-trip, PPT-P2, XLS-S1, XLS-S2, pre-phase architecture, cross-suite and aggregate stability-freeze gates. The new freeze candidate was then validated at commit `7e852032e21a35710e4fcb3a0c33d0f76ff609e6`; aggregate Stability freeze regression run `34458997715` completed successfully, together with the candidate integrity/update, architecture, EPUB, Plain Text, Spreadsheets and cross-suite workflows triggered by the final metadata/contract diff.

The format-preservation policy remains conservative: unsupported OOXML/package content is preserved where the existing package-preserving contracts support it, while legacy or unsupported editable semantics are not silently claimed as fully supported.

## Frozen gate

`STABILITY_STATE.json` is now inactive with `currentWorkspace: freeze` and `freezeCandidate.status: frozen`. The candidate gate commit and run above are the evidence authorizing this transition. The final metadata-only frozen checkpoint must also remain green under the aggregate gate; any red final run invalidates closure until explained and corrected.

## Post-freeze rule

The domestic-use roadmap has reached its final Freeze phase. Future user-test bug fixes or remediation work must preserve the frozen stability contracts and must not broaden format-fidelity claims without new regression evidence.
