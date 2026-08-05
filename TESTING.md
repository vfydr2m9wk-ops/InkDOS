# Testing Guide

Repository integrity, privacy leakage, broken local links, malformed fixtures and browser opening regressions are release-blocking.

## Exact commands

```bash
python3 scripts/validate_repository.py
python3 scripts/audit_source.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/run_browser_regressions.py
python3 scripts/run_release_validation.py
python3 scripts/build_release.py --output-dir dist
```

Equivalent npm commands are available as `npm run validate`, `npm run audit`, `npm test`, `npm run test:browser`, `npm run test:release` and `npm run release:build`.

## Automated scope

- Every distributable path is checked for missing local references, stale filenames, exact duplicate files and version mismatches.
- Text, OOXML, PDF and PNG metadata are scanned for personal identifiers, local paths, stale project names and unexpected author fields.
- Synthetic fixtures validate DOCX A4/header/footer/tables, BIFF8 XLS styles/borders/merges, PPTX direct image backgrounds/tables and PDF object-URL opening.
- The service-worker application shell and all workspace routes are checked.
- Release ZIP creation is deterministic and excludes `dist`, `.git`, caches and Python bytecode.

## Manual validation

Use `docs/MANUAL_DEVICE_CHECKLIST.md`. Record unavailable browsers/devices as **Not tested** rather than inferring support.
