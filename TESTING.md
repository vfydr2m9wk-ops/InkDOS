# Testing guide — InkDesk v0.20.2.1

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

- 219 Python unit/package tests pass in the v0.20.2.1 correction-2 audit tree, including DOM-control contracts and regressions for the latest hosted failures.
- First-party JavaScript syntax passes.
- Twelve Chromium browser-regression entry points are configured. The latest hosted v0.20.2.1 run passed 10/12; the two failures were isolated to a legacy title assertion in cross-workspace isolation and a real blank-PDF resize race, both covered by correction 2.
- The dedicated stable-origin recovery case is configured but is recorded as
  **not performed** when the construction environment blocks local HTTP origins.
- Firefox, native WebKit/Safari, iPadOS, Edge and installed-PWA behavior remain
  explicit matrix/manual checks; unavailable engines are never inferred from
  Chromium results.
- The launch/offline HTTP fixtures use daemon request threads so completed tests
  no longer wait on lingering server connections.
- Full incremental-package validation invokes the complete release gate once; it
  does not repeat repository, audit or unit-test stages before that gate.

Record unavailable browsers or devices as **not performed**. Never infer
compatibility from another engine.

## Python validation dependencies

Before running the complete Python suite in a clean environment, install the
pinned validation dependencies:

```bash
python3 -m pip install --disable-pip-version-check --no-cache-dir   -r requirements-ci.txt
```

These packages are test and release-validation dependencies. They are not
loaded by the browser application at runtime.
## v0.20.2.1 functional-correction validation

- `python3 -m unittest tests.test_local_recovery` validates the IndexedDB recovery contract and workspace wiring.
- `python3 tests/browser/revalidate_v0202_local_recovery.py` behaviorally restores unsaved work when the browser environment permits a stable origin.
- `python3 scripts/run_browser_matrix.py` runs the full suite across installed Chromium, Firefox and WebKit engines.
- `python3 tests/browser/revalidate_v02021_functional_corrections.py` verifies Home cleanup, editable Spreadsheet/Presentation filenames, PDF badge removal, and compact TXT/EPUB title-bar height.


## Functional acceptance checklist

- `docs/FUNCTIONAL_ACCEPTANCE_MATRIX.json` inventories every visible interactive control in the Home screen and six workspaces.
- `tests/test_functional_acceptance_matrix.py` fails when a visible control is added or removed without updating the inventory.
- A matrix entry marked `automated` must name regression evidence. `scheduled` means the control is known but does not yet have dedicated behavioral proof.
- `tests/browser/revalidate_presentations_controls.py` is the first control-by-control behavioral gate and specifically covers the responsive Presentations format panel.

- Presentations format-panel cascade regression: verifies desktop visibility plus compact fixed-drawer open/close behavior after the shared Office shell cascade.



#### Presentations control acceptance correction 4

The Format panel and Presenter Notes now have an explicit closed-at-open contract. The browser regression starts from that state and must prove that the visible View controls open, hide, and reopen the Format panel, that format controls mutate a selected object, and that Presenter Notes toggle reversibly. This prevents a correct collapsed startup state from being mistaken for a broken panel while still catching an unresponsive button.


#### Correction 5 deep audit

- The accepted v0.20.2 baseline reached 210 unit tests and 11/11 Chromium browser scripts. The first full v0.20.2.1 validation reached 217 unit tests and 10/12 browser scripts before correction 2 addressed the two new failures.
- Presentations now uses a single `inspectorOpen` state; desktop `hide-inspector` and compact `inspector-open` are derived classes, not independent state.
- The behavioral regression includes a fresh compact/iPad-width cold start, desktop-to-compact breakpoint reconciliation, button accessibility state, Escape closing, and real object-format mutation.
- `tests/test_interactive_dom_contracts.py` checks duplicate ids and direct app `$()` references across Documents, Spreadsheets, Presentations, PDF, TXT and EPUB.

- v0.20.2.1 correction 2 permanently covers blank-PDF resize/pagehide safety and editable-title cross-workspace isolation.
