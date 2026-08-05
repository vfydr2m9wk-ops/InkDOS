# Validation — 0.19.3-beta.4

## Scope

This validation record covers the PDF-only corrective patch. No runtime changes were made to Documents, Spreadsheets or Presentations.

## Automated commands

- `python3 scripts/validate_repository.py`
- `python3 scripts/audit_source.py`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 scripts/run_browser_regressions.py`

## PDF regression expectations

The synthetic three-page PDF must retain its outline and AcroForm markers. The synthetic long PDF must contain exactly 4,000 pages with Author, Creator and Producer set to `InkDesk QA`.

In Chromium automation, opening the long fixture must:

- identify 4,000 pages;
- retain only one iframe under `#nativeMount`;
- render no more than 61 `.page-item` entries;
- apply a direct navigation target containing `#page=3500`;
- support 50% and 400% zoom selections;
- return from full screen without leaving the body in immersive mode;
- produce no JavaScript page errors.

## Privacy

No user-supplied private document is part of the fixture set. Release manifests and checksums are regenerated after validation. Physical Safari/WebKit and iPadOS validation remains manual and is not implied by Chromium results.

## Result recorded for this package

All four automated commands completed successfully on 2026-08-05. The repository unit suite reported 14 passing tests. Chromium regressions passed for DOCX, XLS, PPTX and both PDF fixtures, including the direct page-3,500 target on the synthetic 4,000-page file. No physical Safari/WebKit or iPadOS result is claimed.
