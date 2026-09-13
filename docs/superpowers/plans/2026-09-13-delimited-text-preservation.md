# Delimited Text Preservation Correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open valid semicolon/comma/tab-delimited text into the correct Spreadsheet grid and save/share it back using the original delimiter and supported text conventions without silent conversion or data loss.

**Architecture:** Keep `DelimitedText` as the single parser/serializer authority. Add quote-aware delimiter detection and source text metadata there; let `FileOpenController` request detection for CSV and fixed tab for TSV; let `SaveController` serialize from persisted metadata rather than extension assumptions. Preserve the existing XLSX compatibility gate.

**Tech Stack:** Static JavaScript, Python contract tests invoking Node, Playwright browser regressions, existing InkDOS Spreadsheet session/model.

**Spec:** `docs/superpowers/specs/2026-09-13-delimited-text-preservation-correction-design.md`

## Global Constraints

- User-approved pre-release intervention; Goal 3 remains frozen at `6161eb20f7b5d8d7e58214c38c7c65202abe24c1` until the full intervention gate is green.
- Never commit the user's uploaded CSV; use synthetic equivalent data only.
- CSV same-format save must preserve detected delimiter; TSV remains tab-delimited.
- Preserve literal text, including leading spaces and leading-zero strings.
- Preserve supported BOM/encoding and source line ending/final separator where safely determinable.
- Existing explicit CSV/TSV-to-XLSX conversion safety gate must remain intact.
- No network/backend/telemetry additions.

---

### Task 1: Add RED delimiter/preservation regression coverage

**Files:**
- Modify: `tests/test_spreadsheets_delimited_text_contract.py`
- Test: `tests/test_spreadsheets_delimited_text_contract.py`

**Interfaces:**
- Consumes: current `InkDOS2Spreadsheets.DelimitedText.parse/serialize/compatibility`.
- Produces: executable contract for `detectDelimiter`, metadata-driven delimiter/line-ending preservation, and semicolon round-trip.

- [ ] **Step 1: Extend the Node probe with a synthetic semicolon CSV**

Use privacy-safe source text such as:

```js
const semi='Username; Identifier;First name;Last name\nuser01;1001;Alex;Morgan\nuser02;0007;Taylor;Lee\n';
const semiParsed=codec.parse(enc.encode(semi).buffer,{fileName:'sample.csv'});
```

Assert the grid contains four columns and preserves `' Identifier'` and `'0007'` literally.

- [ ] **Step 2: Add quote-aware detection cases**

Add comma CSV containing quoted semicolons and semicolon CSV containing quoted commas; assert each chooses the structural delimiter rather than quoted punctuation. Add one-column CSV fallback and fixed TSV behavior.

- [ ] **Step 3: Add preservation assertions**

Require `book.delimitedMeta.delimiter`, `lineEnding`, and final-record-separator metadata. Serialize without manually passing a delimiter and assert semicolon/LF round-trip remains semicolon/LF.

- [ ] **Step 4: Run the focused contract and confirm RED**

Run:

```bash
python tests/test_spreadsheets_delimited_text_contract.py
```

Expected: FAIL because current parser defaults CSV to comma and serializer defaults to comma/CRLF.

- [ ] **Step 5: Commit RED test**

```bash
git add tests/test_spreadsheets_delimited_text_contract.py
git commit -m "test(spreadsheets): cover CSV delimiter preservation"
```

---

### Task 2: Implement quote-aware delimiter and text-convention metadata

**Files:**
- Modify: `apps/spreadsheets/io/delimited-text.js`
- Test: `tests/test_spreadsheets_delimited_text_contract.py`

**Interfaces:**
- Produces: `detectDelimiter(text, candidates)` returning `',' | ';' | '\t'`; `parse(input,{delimiter,fileName})` with omitted CSV delimiter invoking detection; `delimitedMeta` carrying delimiter, encoding, BOM, line ending, final separator.
- Consumes: existing `parseRows`, `decode`, workbook cell model.

- [ ] **Step 1: Add logical-record sampling for delimiter scoring**

Implement bounded quote-aware scanning so candidate delimiters inside quoted fields are ignored. Score candidates by stable multi-column counts across a bounded number of logical rows; prefer stable structure, then deterministic candidate order. If no candidate forms convincing multi-column structure, return comma.

- [ ] **Step 2: Detect text convention before parsing**

From decoded text determine `lineEnding` as `\r\n`, `\n`, or `\r` using the first unquoted record separator, and record whether source text ends with a record separator.

- [ ] **Step 3: Expand allowed delimiters**

Allow `,`, `;`, and `\t`. For `.tsv`, callers continue to pass tab explicitly. For `.csv` with omitted delimiter, call `detectDelimiter`.

- [ ] **Step 4: Persist metadata on both sheet and workbook**

Store:

```js
{rows,cols,bom,encoding,delimiter,lineEnding,finalRecordSeparator}
```

without trimming field content.

- [ ] **Step 5: Run focused contract**

```bash
python tests/test_spreadsheets_delimited_text_contract.py
```

Expected: parser/detection assertions pass; save-path integration may still fail until Task 3.

- [ ] **Step 6: Commit parser implementation**

```bash
git add apps/spreadsheets/io/delimited-text.js tests/test_spreadsheets_delimited_text_contract.py
git commit -m "feat(spreadsheets): detect and preserve CSV delimiters"
```

---

### Task 3: Route CSV open/save through preserved metadata

**Files:**
- Modify: `apps/spreadsheets/io/file-open-controller.js`
- Modify: `apps/spreadsheets/io/save-controller.js`
- Modify: `apps/spreadsheets/io/delimited-text.js`
- Test: `tests/test_spreadsheets_delimited_text_contract.py`

**Interfaces:**
- Consumes: `DelimitedText.parse` auto-detection and `book.delimitedMeta`.
- Produces: same-format Save/Share that uses source delimiter/text convention.

- [ ] **Step 1: Stop forcing comma on CSV open**

Change the delimited open path so TSV passes `delimiter:'\t'`, while CSV calls `parse(buffer,{fileName:file.name})` without a forced comma.

- [ ] **Step 2: Make serializer metadata-driven by default**

In `serialize`, choose delimiter/encoding/BOM/lineEnding/final separator from explicit options first, then `sheet.delimitedMeta`/`book.delimitedMeta`, with safe CSV defaults only when metadata is absent.

- [ ] **Step 3: Stop forcing comma on CSV Save/Share**

`SaveController.prepareBlob()` must call `DelimitedText.serialize(session.book, ...)` using preserved metadata rather than `sourceKind==='csv' ? ',' : '\t'`.

- [ ] **Step 4: Keep conversion gate unchanged**

Confirm formulas, formatting, multiple sheets and other XLSX-only state still require explicit `Convert to XLSX` confirmation.

- [ ] **Step 5: Run focused and conversion contracts**

```bash
python tests/test_spreadsheets_delimited_text_contract.py
python tests/test_spreadsheets_delimited_conversion_guard_contract.py
```

Expected: PASS.

- [ ] **Step 6: Commit open/save integration**

```bash
git add apps/spreadsheets/io/delimited-text.js apps/spreadsheets/io/file-open-controller.js apps/spreadsheets/io/save-controller.js tests/test_spreadsheets_delimited_text_contract.py
git commit -m "fix(spreadsheets): preserve delimited source convention"
```

---

### Task 4: Add browser-level open/edit/save regression

**Files:**
- Create or modify: `tests/test_spreadsheets_delimited_text_browser.py`
- Modify only if needed for test hooks: `apps/spreadsheets/app.js`

**Interfaces:**
- Consumes: real file-open/session/save code paths.
- Produces: browser proof that semicolon CSV is a four-column editable grid and same-format export remains semicolon-delimited.

- [ ] **Step 1: Build an in-memory synthetic File in Playwright**

Use `new File([source], 'sample.csv', {type:'text/csv'})` and invoke the exposed file-open controller/debug path rather than committing a fixture containing user data.

- [ ] **Step 2: Assert four-column grid and literal text**

Verify first row occupies A:D, leading space remains in B1, and `0007` remains text after an edit cycle.

- [ ] **Step 3: Capture same-format serialization**

Use existing debug/session access or a narrow test hook to call the real serializer and assert output still contains semicolon-separated records and source line endings.

- [ ] **Step 4: Run browser matrix**

```bash
BROWSER=chromium python tests/test_spreadsheets_delimited_text_browser.py
BROWSER=firefox python tests/test_spreadsheets_delimited_text_browser.py
BROWSER=webkit python tests/test_spreadsheets_delimited_text_browser.py
```

Expected: PASS on all three.

- [ ] **Step 5: Commit browser regression**

```bash
git add tests/test_spreadsheets_delimited_text_browser.py apps/spreadsheets/app.js
git commit -m "test(spreadsheets): verify semicolon CSV browser roundtrip"
```

---

### Task 5: Verify Spreadsheet and cross-suite safety before density work starts

**Files:**
- No production change unless a verified regression requires one.
- Update checkpoint only after green evidence.

- [ ] **Step 1: Run Spreadsheet contracts relevant to CSV/XLS/XLSX**

```bash
python tests/test_spreadsheets_delimited_text_contract.py
python tests/test_spreadsheets_delimited_conversion_guard_contract.py
```

- [ ] **Step 2: Run cross-suite stability contract**

```bash
python tests/test_cross_suite_stability_contract.py
```

- [ ] **Step 3: Record exact green SHA and advance to adaptive-density plan**

Do not refresh global integrity metadata yet; defer the heavy integrity refresh to the coherent three-part intervention checkpoint unless existing validation requires it earlier.
