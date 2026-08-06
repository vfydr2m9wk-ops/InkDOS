# Testing guide — InkDesk v0.20.0

Every meaningful change requires static validation, targeted tests, and broader
regression. Data corruption, silent save failure, stale export, and
cross-workspace contamination are release-blocking defects.

## Source-package checks

```bash
python3 scripts/generate_module_registry.py --check
python3 scripts/check_no_legacy_runtime.py
python3 scripts/validate_repository.py --allow-vendor-bootstrap
python3 scripts/audit_source.py
python3 scripts/generate_checksums.py
python3 scripts/verify_checksums.py
```

`--allow-vendor-bootstrap` only permits the three pinned PDF.js files to be
absent when `VENDOR_SOURCES.json` is present. It is for the pre-publication
source ZIP. It does not weaken normal validation.

## Published-tree checks

After the publication workflow installs PDF.js, run strict validation:

```bash
python3 scripts/validate_repository.py
python3 scripts/audit_source.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/verify_checksums.py
```

The GitHub workflow runs these commands both before and after repository
replacement.

## Current evidence

- 170 Python unit/package tests passed in a structural validation copy.
- First-party JavaScript syntax passed.
- The source audit passed with two documented large-file refactoring notes and
  one manual dynamic-code review note for the allowlisted spreadsheet formula
  evaluator.
- Real PDF rendering, native Safari/WebKit, Firefox, iPadOS, and installed-PWA
  behavior were not performed in the package-construction environment.

Record unavailable browsers or devices as **not performed**. Never infer
compatibility from another engine.
