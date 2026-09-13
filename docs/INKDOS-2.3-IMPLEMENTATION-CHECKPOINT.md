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

The existing branch work is retained; it is not to be reset merely because the approval gate was clarified. The branch is ahead of `main` and already contains TDD work and Plain Text implementation changes, including the initial RED contract commit `14edf384fee683c6f59817ef9c3a652c1c9515fa` and subsequent follow-up commits.

Current changed Goal 1 areas include:

- `apps/txt/txt-policy.js`
- `apps/txt/io/txt-file-controller.js`
- `apps/txt/editor/editor-controller.js`
- `apps/txt/index.html`
- `tests/test_txt_format_expansion_contract.py`
- historical integrity metadata refresh commits produced before the batch-cadence policy change

## 2026-09-13 Goal 1 continuation checkpoint

- Canonical design/spec materialized and explicitly marked `USER-APPROVED`.
- Goal 1 implementation plan recorded at `docs/superpowers/plans/2026-09-13-inkdos-2.3-goal1-format-coverage.md`.
- CSV/TSV RED codec contract: `d523b830837ff661637c51916cd44df42d6b1e8f`.
- Release-validation registration for the CSV/TSV contract: `dff4bd2c231d4fe2bcc5e4e98a4e759266af8b6e`.
- CSV/TSV codec GREEN implementation: `d3039d7497f4e0a67c4f89b3ac544947a2c5fcc6`.
- Integration RED contract for picker/open/session routing: `1943f332c04874d288350468ac5e70b122b1189e`; CI `InkDOS integrity and update` run 829 failed as expected before integration was complete.
- CSV/TSV source-name/session preservation: `c93d3c7b82c640f0d34169e5301123b5a43b37f0`.
- CSV/TSV file-open routing: `e8c6a2b46c4c90124dd8cb849ee8bb619d1f986f`.
- Spreadsheets picker/script graph integration: `3d661df6a09ca9800bd37d45573dbec53451dc1d`.
- Last pre-policy automated integrity checkpoint: `135810d451af6f8e4befabc1d23a5affd2bba379`.

### Tests/evidence

- The codec RED was reproduced because `apps/spreadsheets/io/delimited-text.js` did not exist.
- The codec behavior test then passed after implementation for quoted fields, embedded delimiters, embedded newlines, escaped quotes, UTF-8 BOM round-trip, TSV delimiter handling, and leading-zero strings.
- CI after the integration RED contract reported failure, confirming the test was exercising missing integration rather than passing against pre-existing behavior.
- Automatic integrity refresh after source changes is now intentionally disabled; the next full integrity refresh belongs to the coherent Goal 1 checkpoint.

### Current blocker before the next Goal 1 TDD cycle

`apps/spreadsheets/index.html` now loads `io/delimited-text.js`, but `service-worker.js` does not yet include `./apps/spreadsheets/io/delimited-text.js` in `APP_SHELL`. The existing Spreadsheets stability contract requires all local scripts referenced by the workspace to be present in the offline shell. Therefore Goal 1 is intentionally not marked complete and the save/conversion work must not be treated as verified until the offline-shell inconsistency is corrected and the relevant targeted checks pass.

## Next work

Continue Goal 1 from this checkpoint. First synchronize the Spreadsheets offline shell with `io/delimited-text.js` and run the focused contracts. Then proceed with TDD for same-format CSV/TSV save and the explicit XLSX-conversion warning/guard for features not representable in CSV/TSV. Continue implementing the complete Goal 1 scope before the next heavy GitHub checkpoint. Do not begin Goal 2 until Plain Text plus CSV/TSV behavior is verified against the canonical spec.

At the end of each Goal, update this document with the final head SHA, tests executed, pass/fail state, blockers/limitations, and the checkpoint validation result.
