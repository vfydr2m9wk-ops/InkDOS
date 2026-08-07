# Testing guide — InkDesk v0.20.2.5

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

- Architecture guardrails pass with 49 runtime JS/CSS files and the Presentations `app.js` ratchet reduced again from 870/88 to 868/82 physical/long lines.
- The Python suite contains 235 tests. In the local reconstruction, 234 pass; the checksum-manifest test is the only local hold. Its five reported baseline discrepancies are the two hosted-tree files not reproduced byte-for-byte locally (`apps/pdf/app.js` and `RELEASE_NOTES_0.20.2.1.md`) plus the three pinned PDF.js publication files absent from this environment. The hosted repository remains the authoritative checksum gate.
- `revalidate_v0201_consistency.py` and the manual-script harnesses load both state controllers plus all three UI controllers before `app.js`.
- `revalidate_pptx_three_eras.py` passes 18/18 compatibility and round-trip checks.
- Cross-workspace isolation and transactional-open browser regressions pass with zero Presentations page errors.
- Launch/offline validation passes static-asset and restricted-API/touch-emulation checks; local HTTP/file navigation can be reported as not performed when blocked by the execution environment.
- The dedicated `revalidate_presentations_controls.py` remains the hosted behavior gate for Format-panel open/hide/reopen, formatting changes, selection clear/reselect, Undo/Redo restoration, compact drawer state and Escape handling. Local HTTP navigation was blocked by the execution environment, so this expanded path is not claimed locally.
- Firefox, native WebKit/Safari, iPadOS, Edge and installed-PWA behavior remain explicit matrix/manual checks; unavailable engines are never inferred from Chromium results.

## Python validation dependencies

Before running the complete Python suite in a clean environment, install the
pinned validation dependencies:

```bash
python3 -m pip install --disable-pip-version-check --no-cache-dir   -r requirements-ci.txt
```

These packages are test and release-validation dependencies. They are not
loaded by the browser application at runtime.
## v0.20.2.2 functional-correction validation

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

- Latest hosted correction-4 run: 205 unit tests passed and 10/11 Chromium browser scripts passed. The remaining failure was a compact breakpoint mismatch between the panel's visual state and `aria-expanded`.
- Presentations now uses a single `inspectorOpen` state; desktop `hide-inspector` and compact `inspector-open` are derived classes, not independent state.
- The behavioral regression includes a fresh compact/iPad-width cold start, desktop-to-compact breakpoint reconciliation, button accessibility state, Escape closing, and real object-format mutation.
- `tests/test_interactive_dom_contracts.py` checks duplicate ids and direct app `$()` references across Documents, Spreadsheets, Presentations, PDF, TXT and EPUB.

## v0.20.2.2 architecture guardrails

`python3 scripts/check_architecture_guardrails.py` validates runtime file-size
and physical-line debt, workspace dependency direction and relative import
cycles. It is part of `scripts/run_release_validation.py`.

## v0.20.2.5 Presentations decomposition

- `tests/test_presentations_modularization.py` verifies the selection/history state controllers plus Inspector, thumbnail and presenter-notes UI controllers as focused components loaded before `app.js`, within new-source limits and precached offline.
- The Presentations `app.js` ratchet is 868 physical lines / 82 long lines; selection/drag and history stacks may not be reimplemented in the entry point.
- Browser harnesses that strip HTML script tags explicitly load both Presentations state controllers and all three UI controllers before `app.js`.
- `tests/browser/revalidate_presentations_controls.py` remains the user-visible behavior gate for Format, notes and thumbnail visibility, compact-width behavior, selection clear/reselect, and Undo/Redo snapshot restoration.
- Existing PPTX, recovery, cross-workspace and transactional-open browser regressions must remain unchanged.
