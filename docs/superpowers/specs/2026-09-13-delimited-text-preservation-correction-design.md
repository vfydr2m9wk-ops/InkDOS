# InkDOS 2.3 Delimited Text Preservation Correction

## Status

**NEEDS USER REVIEW — RUNTIME DEVELOPMENT FROZEN**

This is a required pre-release correction to the Goal 1 CSV/TSV support. It is part of the same temporary intervention that freezes Goal 3 at:

`6161eb20f7b5d8d7e58214c38c7c65202abe24c1`

No Goal 3 implementation is discarded. Goal 3 resumes automatically after the adaptive-density, delimited-text, and Presentations functional corrections are validated.

## Confirmed defect

The current Spreadsheet delimited-text implementation treats every `.csv` file as comma-delimited and every `.tsv` file as tab-delimited.

The user supplied a real CSV whose first row is:

`Username; Identifier;First name;Last name`

The file is UTF-8 text and uses semicolon (`;`) as its field delimiter. Microsoft Excel opens it as four columns. InkDOS currently forces comma for `.csv`, so this valid CSV is parsed incorrectly.

The save path has the same defect: every CSV is serialized with comma even if the source used another valid delimiter. Therefore simply fixing import would still allow a same-format save to silently rewrite the delimiter convention.

## Product requirement

Goal 1 promised editable CSV/TSV with same-format preservation where safe. For InkDOS 2.3, a CSV must not be defined as "comma only" in the implementation.

The correction must preserve the source file's delimited-text convention where it can be identified safely.

## Import behavior

### TSV

`.tsv` remains tab-delimited by definition for the normal path.

### CSV

For `.csv`, InkDOS must detect the delimiter from the decoded text rather than forcing comma.

Supported CSV delimiter candidates for 2.3:

- comma `,`
- semicolon `;`
- tab `\t` when a file with a `.csv` extension actually contains a stable tabular tab-separated structure

The detector must be quote-aware. Delimiters inside quoted fields must not be counted as column separators.

The detector should inspect a bounded sample of logical records and prefer the candidate that produces a stable multi-column shape across records. It must not use a naive `split()` or raw character count.

If no candidate produces convincing multi-column structure, fall back conservatively to comma so a legitimate one-column CSV still opens instead of being rejected.

## Preservation metadata

The chosen delimiter becomes part of the workbook/session delimited metadata.

At minimum the metadata required for same-format preservation is:

- source kind: CSV or TSV
- delimiter
- detected/supported encoding
- BOM presence
- source line-ending convention when determinable
- whether the source ended with a final record separator when practical to preserve

The source filename and extension remain unchanged by default.

## Save behavior

Same-format save/share must use the stored source delimiter.

Examples:

- comma CSV opens and saves as comma CSV;
- semicolon CSV opens and saves as semicolon CSV;
- TSV opens and saves with tabs.

Saving a semicolon CSV as comma CSV without an explicit format-conversion action is not acceptable.

The existing CSV/XLSX compatibility gate remains in force. Unsupported workbook features still require explicit conversion to XLSX rather than silent flattening.

## Encoding and line endings

Existing supported BOM/encoding preservation must remain green.

The correction should also avoid unnecessary line-ending normalization. If the source convention can be determined safely (`CRLF`, `LF`, or `CR`), store it and reuse it on same-format export.

Do not silently replace undecodable text. If an unsupported/ambiguous byte encoding cannot be decoded without replacement/data loss, fail clearly rather than corrupting cell text.

Broad legacy-codepage support is not required unless implemented with deterministic round-trip tests.

## Parsing requirements

The existing real parser behavior remains required:

- quoted delimiters;
- embedded line breaks inside quoted fields;
- escaped quotes;
- empty fields;
- trailing empty columns;
- leading-zero strings preserved as text;
- no destructive number/date coercion for plain CSV/TSV text entry;
- deterministic serialization.

Delimiter detection must not weaken any of those guarantees.

## Real regression

The supplied semicolon CSV must be represented by a synthetic privacy-safe regression fixture with equivalent structure, not by committing the user's uploaded file.

Required expected grid:

- row 1: `Username` | ` Identifier` | `First name` | `Last name`
- following rows remain four columns with their literal textual values

The leading space before `Identifier` is source data and must not be silently trimmed merely because the delimiter was detected.

## Tests

Add focused tests for:

1. semicolon CSV detection;
2. comma CSV remains comma;
3. quoted commas do not cause a semicolon CSV to be misdetected;
4. quoted semicolons do not cause a comma CSV to be misdetected;
5. multiline quoted fields remain one field;
6. TSV remains tab-delimited;
7. one-column CSV falls back safely;
8. detected delimiter is retained in metadata;
9. semicolon CSV save uses semicolon;
10. open → edit → save → reopen preserves the same tabular structure and delimiter convention;
11. BOM/encoding regressions remain green;
12. line-ending convention is preserved where supported;
13. existing CSV/TSV conversion-to-XLSX safety gate remains green.

Run the relevant Spreadsheet contract/browser regressions in Chromium, Firefox, and WebKit as part of the coherent pre-release intervention checkpoint.

## Release blocking criteria

InkDOS 2.3 must not ship if:

- a valid semicolon-delimited CSV opens as one column;
- same-format save changes a detected semicolon CSV to comma without explicit user conversion;
- delimiter detection breaks quoted fields or multiline records;
- delimiter/encoding changes cause silent data loss;
- existing XLS/XLSX/CSV/TSV Spreadsheet behavior regresses.

## Intervention sequence

Because data correctness takes precedence over cosmetic refinement, the temporary intervention sequence is:

1. correct CSV/TSV delimiter and same-format preservation behavior;
2. implement adaptive Auto/Desktop/Mobile frame density;
3. implement Presentations text-overflow and object-selection/movement corrections;
4. run focused and cross-workspace/browser validation;
5. refresh integrity/checksum metadata at the coherent checkpoint;
6. record intervention completion;
7. automatically resume Goal 3 from the preserved work and diagnostic evidence;
8. continue Goal 3 → Goal 4 → final InkDOS 2.3 validation/release.

No runtime implementation starts until this correction and the combined pre-release intervention are explicitly user-approved.