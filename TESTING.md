# Testing Guide

Data loss, false save confirmation, active-content injection, dynamic formula compilation, package ambiguity, unexpected OOXML part loss, and cross-workspace state leakage are release-blocking.

## Exact commands

```bash
python3 scripts/verify_checksums.py
python3 scripts/validate_repository.py
python3 scripts/audit_source.py
python3 -m unittest discover -s tests -p "test_*.py"
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group package-security
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group lifecycle
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group isolation-offline
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group documents-presentations
PLAYWRIGHT_BROWSER=chromium python3 scripts/run_browser_regressions.py --group spreadsheets
python3 scripts/run_release_validation.py
python3 scripts/build_release.py --output-dir dist
```

For additional Playwright engines:

```bash
PLAYWRIGHT_BROWSER=firefox python3 scripts/run_browser_regressions.py --group package-security
PLAYWRIGHT_BROWSER=webkit python3 scripts/run_browser_regressions.py --group package-security
```

## Automated scope

- File lifecycle: dirty, preparing, unverified download, failure, repeated exports, before-unload warning, fingerprint-based reopen verification, and workspace isolation.
- DOCX DOM security: hostile event attributes, protocols, external images/styles, SVG/embedded content, clobbering names, malformed relationships, and no unexpected network request.
- Formula parser: zero values, precedence, unary operators, parentheses, malformed input, length/token/depth/step limits, unsupported identifiers/functions, division by zero, cycles, and injection strings.
- ZIP/XML: duplicates, path collisions, traversal, local/central mismatch, overlap, methods, encryption, ZIP64, truncation, entry/size/ratio limits, DTD/entity rejection, malformed XML, aggregate XML budget, depth, nodes, and attributes.
- OOXML: open-edit-export-reopen for representative DOCX/XLSX/PPTX fixtures, package-inventory preservation, failure paths, and no-network assertions in browser scenarios.
- Service worker: shell inventory, same-origin behavior, and restricted-API fallback checks.
- Release: deterministic archive generation, required notices, exact commit metadata, exclusions, and archive checksum.

A fixture’s existence, source-code grep, or ZIP listing alone is not a successful round trip. A supported round-trip test must open, edit, export, reopen, verify the edit, compare expected package parts, and assert no unexpected network request.

## Manual validation

Use `docs/MANUAL_DEVICE_CHECKLIST.md`. Every row must be marked Passed, Failed, Partially passed, or Not tested. Never convert “Not tested” into a support claim.
