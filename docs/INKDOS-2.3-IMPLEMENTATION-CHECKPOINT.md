# InkDOS 2.3 Implementation Checkpoint

## Canonical state

- Canonical spec: `docs/superpowers/specs/2026-09-13-inkdos-2.3-design.md`
- Approval: `USER-APPROVED`
- Base `main` before this pass: `4d9b21478309f84d1437605cd57b55744643b882`
- Existing InkDOS 2.3 branch before approval materialization: `feature/inkdos-2.3` at `3712d8d296bae8d486fa92c43d280c8907f90759`
- Open development PR: #132, `InkDOS 2.3 Goal 1 — format expansion`

## Sequence state

The sequence is fixed and must not be restarted or reordered.

1. Goal 1 — editable format coverage: **IN PROGRESS**
2. Goal 2 — PPTX/PowerPoint fidelity: **NOT STARTED**
3. Goal 3 — desktop associations/launchers/native windows: **NOT STARTED**
4. Goal 4 — manual-only updater: **NOT STARTED**

## Preserved Goal 1 work

The existing branch work is retained; it is not to be reset merely because the approval gate was clarified. The branch is ahead of `main` and already contains TDD work and Plain Text implementation changes, including the initial RED contract commit `14edf384fee683c6f59817ef9c3a652c1c9515fa` and subsequent follow-up commits.

Current changed Goal 1 areas include:

- `apps/txt/txt-policy.js`
- `apps/txt/io/txt-file-controller.js`
- `apps/txt/editor/editor-controller.js`
- `apps/txt/index.html`
- `tests/test_txt_format_expansion_contract.py`
- integrity metadata refreshed by repository automation

## Next work

Continue Goal 1 from the current branch checkpoint. Do not begin Goal 2 until Plain Text plus CSV/TSV behavior is verified against the canonical spec, including original-extension preservation, real CSV/TSV parsing/serialization, leading-zero protection, BOM/encoding handling, and explicit XLSX conversion warnings for unsupported features.

Every substantive checkpoint must update this document with exact head SHA, tests executed, pass/fail state, and blockers.
