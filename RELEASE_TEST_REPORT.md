# Release Test Report — InkDesk 0.19.1-beta

## Baseline

- Upstream `main` commit inspected: `538c99d7c09566644d2095aaf33305b890a4b4c7`.
- Version found: `0.19.0-beta`.
- Source archive SHA-256: `9152bc3051860c4067ecbfc30125b26199755cea07aa7126736e0a3549d842be`.
- Baseline checksum verification, repository validation, source audit, and 43 unit/package tests passed.
- The original aggregate Chromium runner stalled at the cross-workspace scenario in this constrained environment; scenarios were isolated during implementation.

## Final executed evidence

| Exact command | Result | Count | Failures | Skipped/unavailable |
|---|---|---:|---:|---|
| `python3 scripts/validate_repository.py` | Passed | 8 HTML; 5 JSON/manifest | 0 | 0 |
| `python3 scripts/audit_source.py` | Passed | Source audit | 0 | 0 |
| `node tests/js/security-modules.test.js` | Passed | 46 assertions | 0 | 0 |
| `python3 -m unittest discover -s tests -p "test_*.py"` | Passed | 49 tests | 0 | 0 |
| `PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group package-security` | Passed | 2 scripts | 0 | 0 |
| `PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group lifecycle` | Passed | 3 scripts | 0 | 0 |
| `PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group isolation-offline` | Passed | 2 scripts | 0 | 0 |
| `PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group documents-presentations` | Passed | 2 scripts | 0 | 0 |
| `PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group spreadsheets` | Passed | 2 scripts | 0 | 0 |
| `PLAYWRIGHT_BROWSER=chromium python3 tests/browser/revalidate_unified_open_router.py` | Passed | DOCX/XLSX/PPTX mapping, embedded file bridge, 3 home-link targets | 0 | 0 |
| `python3 -m unittest tests.test_release_packaging -v` | Passed | 1 deterministic-package test | 0 | 0 |
| `PLAYWRIGHT_BROWSER=firefox ...revalidate_hardening_controls.py` | Not executable locally | — | — | Firefox executable missing |
| `PLAYWRIGHT_BROWSER=webkit ...revalidate_hardening_controls.py` | Not executable locally | — | — | WebKit executable missing |
| Native Safari / iPadOS / installed PWA | Not tested | — | — | Device/browser unavailable |

Final checksum verification passed for 163 repository files after the navigation and home-layout enhancements. The release archive is generated from the final commit and carries its own SHA-256 checksum and build metadata.
