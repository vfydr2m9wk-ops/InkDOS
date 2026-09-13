# InkDOS 2.3 Implementation Checkpoint

## Canonical state

- Canonical spec: `docs/superpowers/specs/2026-09-13-inkdos-2.3-design.md`
- Approval: `USER-APPROVED`
- Current `main` observed before the 2026-09-13 formula/paste guard mutation: `9b1848629e8a86c4513785595014ab32fe168a06`
- Open development PR: #132, `InkDOS 2.3 Goal 1 — format expansion`
- Goal 1 branch: `feature/inkdos-2.3`

## Sequence state

The sequence is fixed and must not be restarted or reordered.

1. Goal 1 — editable format coverage: **IN PROGRESS**
2. Goal 2 — PPTX/PowerPoint fidelity: **NOT STARTED**
3. Goal 3 — desktop associations/launchers/native windows: **NOT STARTED**
4. Goal 4 — manual-only updater: **NOT STARTED**

## Development cadence — USER-APPROVED 2026-09-13

InkDOS 2.3 is developed in coherent Goal-sized batches rather than as a sequence of GitHub micro-checkpoints.

- Continue implementing within the current Goal without waiting for GitHub Actions after each small TDD step.
- Targeted/local tests remain mandatory while implementing risky or data-preservation behavior.
- Do not refresh integrity metadata automatically after each feature/fix push.
- Run the integrity metadata refresh manually at a coherent Goal checkpoint.
- Run the full GitHub validation suite at Goal checkpoints and after integration to `main`, not on every draft-PR synchronization.
- Keep the development PR in draft while the Goal is incomplete.
- Preserve the approved order: Goal 1 → Goal 2 → Goal 3 → Goal 4 → final 2.3.0 validation.
- A Goal is not complete until its acceptance criteria and relevant regression coverage have been reviewed, even though intermediate GitHub Actions are intentionally reduced.

## Preserved Goal 1 work

The existing branch work is retained; it is not to be reset merely because the approval gate was clarified. The initial Goal 1 RED contract commit `14edf384fee683c6f59817ef9c3a652c1c9515fa` and all subsequent work remain in branch history.

### Plain Text

Plain Text format expansion is implemented for the approved raw-text family while retaining extension-preserving save behavior and explicit unsupported-format rejection.

### CSV/TSV codec and integration

Completed Goal 1 work includes:

- CSV/TSV RED codec contract: `d523b830837ff661637c51916cd44df42d6b1e8f`.
- Release-validation registration for the CSV/TSV contract: `dff4bd2c231d4fe2bcc5e4e98a4e759266af8b6e`.
- CSV/TSV codec GREEN implementation: `d3039d7497f4e0a67c4f89b3ac544947a2c5fcc6`.
- Integration RED contract for picker/open/session routing: `1943f332c04874d288350468ac5e70b122b1189e`.
- CSV/TSV source-name/session preservation: `c93d3c7b82c640f0d34169e5301123b5a43b37f0`.
- CSV/TSV file-open routing: `e8c6a2b46c4c90124dd8cb849ee8bb619d1f986f`.
- Spreadsheets picker/script graph integration: `3d661df6a09ca9800bd37d45573dbec53451dc1d`.
- Last pre-policy automated integrity checkpoint: `135810d451af6f8e4befabc1d23a5affd2bba379`.
- Same-format CSV/TSV Save/Share behavior, source extension/MIME/delimiter/BOM/encoding preservation where supported, explicit CSV/TSV → XLSX conversion, and representability guards for formatting/merges/dimensions/worksheet add-delete are present on the current branch before the formula/paste guard cycle.

### Codec evidence already obtained

- The codec RED was reproduced because `apps/spreadsheets/io/delimited-text.js` did not exist.
- The codec behavior test then passed after implementation for quoted fields, embedded delimiters, embedded newlines, escaped quotes, UTF-8 BOM round-trip, TSV delimiter handling, and leading-zero strings.
- The earlier integration RED was observed before its corresponding implementation.

## 2026-09-13 formula/paste representability TDD cycle

The focused RED contract is `tests/test_spreadsheets_delimited_formula_paste_guard_contract.py`. Before production changes, source inspection confirmed the required guard hooks were absent from `apps/spreadsheets/ui/editor-controller.js` and `apps/spreadsheets/ui/formula-bar.js`.

Implemented GREEN candidate changes:

- `fcd8bc1093ab8012044f392c38efa8a5beacacc6` — Formula Bar gained an async `beforeCommit` gate, so formula entry can be canceled before workbook mutation.
- `6af70258f17915938ea2065fe6b4e30bdbb173a0` — direct/grid formula commits, plain-text formula paste, semantic formula/rich-style paste, aggregate formula operations, and percentage formatting now route through the existing explicit `ensureXlsxFor(...)` conversion gate before mutating a CSV/TSV session.
- Ordinary value-only CSV/TSV edits and value-only paste remain on the original delimited format path and do not force conversion.
- Semantic rich-paste detection ignores empty/default style containers but treats formulas, dirty/non-default style state, or nonzero style IDs as XLSX-requiring content.
- Canceling the conversion prompt prevents the guarded formula/style mutation instead of silently degrading or converting the source format.

### Verification state for this cycle

- Source inspection after the writes confirms the RED contract's required hooks/labels are present in both production controllers.
- A local exact-head test execution was attempted by materializing the feature-branch files from `raw.githubusercontent.com`, but the execution environment could not resolve that host (`curl: (6) Could not resolve host: raw.githubusercontent.com`). This is an environment/network limitation, not a test result.
- Therefore the focused contract is **not yet claimed PASS** and Goal 1 remains **IN PROGRESS**.
- No Goal 2 work has started.

## Current branch checkpoint

- Production-code head after the formula/paste guard implementation: `6af70258f17915938ea2065fe6b4e30bdbb173a0`.
- The branch was based on PR-head `9d6bed792cba03e705cef2a04012bd4016bc5eb7` for this TDD cycle.
- The current `main` observed before mutation was `9b1848629e8a86c4513785595014ab32fe168a06`.
- PR #132 remains the Goal 1 development PR.

## Next work

Remain in Goal 1. Execute the focused formula/paste guard contract as soon as an exact-head runnable environment is available, fix any resulting regression before expanding scope, then complete the remaining Goal 1 representability review. At the coherent Goal 1 checkpoint, reconcile current `main` policy changes, refresh integrity metadata once, run the relevant cross-platform/repository validation suite, update this document with final exact SHAs/tests/results, and only then unlock Goal 2.

At the end of each Goal, update this document with the final head SHA, tests executed, pass/fail state, blockers/limitations, and checkpoint validation result.
