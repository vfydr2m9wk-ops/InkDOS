# InkDOS 2.3 Implementation Checkpoint

## Canonical state

- Canonical spec: `docs/superpowers/specs/2026-09-13-inkdos-2.3-design.md`
- Approval: `USER-APPROVED`
- Current `main`: `9b1848629e8a86c4513785595014ab32fe168a06`
- Open development PR: #132, `InkDOS 2.3 Goal 1 — format expansion`
- Canonical development branch: `feature/inkdos-2.3`

## Sequence state

The sequence is fixed and must not be restarted or reordered.

1. Goal 1 — editable format coverage: **COMPLETE — VERIFIED**
2. Goal 2 — PPTX/PowerPoint fidelity: **READY — NOT STARTED**
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
- Same-format CSV/TSV Save/Share behavior, source extension/MIME/delimiter/BOM/encoding preservation where supported, explicit CSV/TSV → XLSX conversion, and representability guards for formatting/merges/dimensions/worksheet add-delete are present.
- Direct-edit leading-zero/text preservation RED: `b4ba14c1af81d00d0c3b05326c21a68a82915741`.
- Direct-edit preservation implementation: `634688a3a731c3af5730370341f55d3286af8e93`.
- Direct-edit preservation contract registration: `96b68b76d5938844a41bf3124b2c2c16f29ec652`.

### Codec evidence

- The codec RED was reproduced because `apps/spreadsheets/io/delimited-text.js` did not exist.
- The codec behavior test then passed after implementation for quoted fields, embedded delimiters, embedded newlines, escaped quotes, UTF-8 BOM round-trip, TSV delimiter handling, and leading-zero strings.
- The earlier integration RED was observed before its corresponding implementation.

## 2026-09-13 formula/paste representability TDD cycle

The focused RED contract is `tests/test_spreadsheets_delimited_formula_paste_guard_contract.py`. Before production changes, source inspection confirmed the required guard hooks were absent from `apps/spreadsheets/ui/editor-controller.js` and `apps/spreadsheets/ui/formula-bar.js`.

Implemented GREEN changes:

- `fcd8bc1093ab8012044f392c38efa8a5beacacc6` — Formula Bar gained an async `beforeCommit` gate, so formula entry can be canceled before workbook mutation.
- `6af70258f17915938ea2065fe6b4e30bdbb173a0` — direct/grid formula commits, plain-text formula paste, semantic formula/rich-style paste, aggregate formula operations, and percentage formatting route through the explicit `ensureXlsxFor(...)` conversion gate before mutating a CSV/TSV session.
- Ordinary value-only CSV/TSV edits and value-only paste remain on the original delimited format path and do not force conversion.
- Semantic rich-paste detection ignores empty/default style containers but treats formulas, dirty/non-default style state, or nonzero style IDs as XLSX-requiring content.
- Canceling the conversion prompt prevents the guarded formula/style mutation instead of silently degrading or converting the source format.

## 2026-09-13 encoding-preservation TDD cycle

Representability review found a concrete encoding metadata defect: UTF-16LE/UTF-16BE bytes and BOM were preserved by the delimited serializer, but the generated Blob MIME type always declared `charset=utf-8`.

- RED reproduced against the pre-fix codec: parsing a BOM-marked UTF-16LE CSV returned `encoding=utf-16le`, but serializing it produced `text/csv;charset=utf-8`.
- RED contract committed first: `060eba634d7f11fa98be0f36ff4b1c6e6329b040`, `tests/test_spreadsheets_delimited_encoding_contract.py`.
- Minimal production fix: `5aec957fe55f7c9a50b37481df3e9d6acb45f157` now derives the CSV/TSV MIME charset from the actual preserved encoding.
- Focused behavior probes after the fix passed for UTF-16LE, UTF-16BE, BOM preservation, leading-zero string preservation, and the existing UTF-8 CSV round-trip/MIME behavior.
- All Goal 1 focused contracts, including Plain Text, codec, encoding, same-format save, conversion guards, formula/paste guards, and direct-edit preservation, are registered in `scripts/run_release_validation.py`.

## Main ancestry reconciliation

Current `main` advanced by workflow-policy commits during Goal 1. Before reconciliation, the affected workflow files were verified byte-identical by blob SHA between the branch and current `main`. A no-content merge commit `addaa0d707835b072925ae5926684f87823f9fa9` reconciled the Goal 1 branch with `main` `9b1848629e8a86c4513785595014ab32fe168a06` without discarding Goal 1 work.

## Goal 1 final verification — 2026-09-13

Systematic debugging of the coherent Goal 1 checkpoint found two stale static contracts rather than product regressions:

- Desktop CI policy contract: fixed in `771f6a2bd13b21e87748411f3cb823d3623a5a89` so the test reflects the approved main/manual-checkpoint build policy instead of requiring a permanent `desktop-tauri` branch trigger.
- Plain Text stability policy authority contract: fixed in `812a1985c7007325b863aa89f2b24f7367b5c6c2` so the stability contract recognizes the approved 2.3 policy authority (`SUPPORTED`, `accept`, `isSupportedName`) without weakening the existing XML/storage authority checks.

Integrity metadata was regenerated and validated after the final test alignment, producing metadata head `00ad69e825794cf74c299df874d273acdf11edca`.

Final canonical validation was GitHub Actions run **#793**, run id `34742310953`, on validation SHA `f91b0fa3119932e3d73ed5e8feacca4e3a5296b4`. All eight jobs completed successfully:

1. Repository contracts — **PASS**
   - clean-snapshot release validation — PASS
   - all static contracts — PASS
   - update trust-boundary regression — PASS
   - security configuration regression — PASS
   - consolidated runtime syntax — PASS
2. Stability browser suite — Chromium — **PASS**
3. Stability browser suite — Firefox — **PASS**
4. Stability browser suite — WebKit — **PASS**
5. Feature browser regressions — Chromium — **PASS**
6. Feature browser regressions — Firefox — **PASS**
7. Feature browser regressions — WebKit — **PASS**
8. Format preservation round-trips — **PASS**

The focused Goal 1 tests were also observed green inside the clean-snapshot/static-contract validation, including:

- Plain Text 2.3 format expansion.
- CSV/TSV codec/routing/save/compatibility.
- UTF-16 encoding/BOM preservation.
- CSV/TSV same-format save.
- explicit XLSX conversion guards.
- formula and semantic-paste guards.
- direct-edit text/leading-zero preservation.

After the validation-trigger commit, the repository's checkpoint-only CI policy was restored in `fffc187e4bc819e33e17f28f5a4a39c2e12b7ec9`. The only difference between validated SHA `f91b0fa3119932e3d73ed5e8feacca4e3a5296b4` and restored-policy SHA `fffc187e4bc819e33e17f28f5a4a39c2e12b7ec9` is `.github/workflows/stability-freeze-regression.yml`, restoring the approved main/manual-checkpoint trigger policy; no runtime/product/test content differs.

### Goal 1 acceptance conclusion

Goal 1 acceptance criteria are **VERIFIED COMPLETE**. Original-format preservation, explicit conversion behavior, browser regressions, repository contracts, and preservation round-trips are green. No Goal 2 production work occurred before this checkpoint.

## Current branch checkpoint

- Goal 1 final validation SHA: `f91b0fa3119932e3d73ed5e8feacca4e3a5296b4`.
- Goal 1 post-validation policy-restored SHA before this documentation update: `fffc187e4bc819e33e17f28f5a4a39c2e12b7ec9`.
- Current `main`: `9b1848629e8a86c4513785595014ab32fe168a06`.
- PR #132 remains draft while the overall InkDOS 2.3 development sequence continues.
- Goal 1: **COMPLETE — VERIFIED**.
- Goal 2: **READY — NOT STARTED**.

## Next work

Proceed to Goal 2 only: diagnose and fix PPTX/PowerPoint fidelity using the supplied real regression first, then focused synthetic regression tests. Use systematic debugging to isolate fidelity root causes and TDD for every production change. Do not begin Goal 3 until Goal 2 has its own verified checkpoint.

At the end of each Goal, update this document with the final head SHA, tests executed, pass/fail state, blockers/limitations, and checkpoint validation result.
