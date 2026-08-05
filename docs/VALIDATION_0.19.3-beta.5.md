# Validation — 0.19.3-beta.5

## Scope

This record covers the PDF-only WebKit embedded-preview hotfix. Documents, Spreadsheets and Presentations runtime files remain unchanged from component version 0.19.3-beta.3.

## Automated commands

- `python3 scripts/validate_repository.py`
- `python3 scripts/audit_source.py`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 scripts/run_browser_regressions.py`

## Repository PDF expectations

The synthetic three-page PDF must retain its outline and AcroForm markers. The synthetic long PDF must contain exactly 4,000 pages with Author, Creator and Producer set to `InkDesk QA`.

Chromium automation must verify:

- one `<object>` and one nested `<embed>` under `#nativeMount`;
- zero PDF iframes;
- at most 61 `.page-item` entries;
- a direct navigation target containing `#page=3500` for the long fixture;
- 50% and 400% zoom selections;
- full-screen exit without a remaining immersive state;
- no JavaScript page errors.

## External regression sample

A user-supplied PDF was tested only from its external sandbox path and was not copied into the repository. Independent PDF inspection reports 13 pages. The InkDesk bounded inspector also reports 13 pages, mounts one object and one embed with zero iframes, and generates a direct `#page=7` target without JavaScript errors.

The sample contains third-party/personal metadata and therefore must not appear in fixtures, release files, screenshots, manifests or checksums.

## Privacy and result boundary

Source auditing, fixture metadata checks and generated manifests must remain clean. Automated Chromium success verifies application state and native-target construction; it does not prove that Safari/iPadOS paints the native PDF surface. A physical target-device retest is required before a general GitHub publication.
