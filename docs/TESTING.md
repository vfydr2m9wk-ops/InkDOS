# Testing guide — InkDesk v0.20.2.17

## v0.20.2.17 Documents ruler interaction decomposition

The hosted package gate must preserve the complete existing behavior suite and additionally verify that ruler pointer-drag ownership is isolated in `shared/ui/document-ruler-drag-controller.js`, the model loads before the drag controller, the drag controller loads before `workspace-layout.js`, offline precache includes all three assets and the architecture ratchet is lowered without changing indentation behavior. Expected unit/package count: 267. Expected Chromium regression count: 17/17.

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

- Architecture guardrails now also retire `shared/office-shell.js` from inherited debt: the shell is 315 physical lines after document-session behavior moved to `shared/ui/document-session-controller.js`; both files are below the normal 500-line ceiling.
- The Python suite contains 267 tests after the Documents ruler-interaction boundary regression was added. The reconstructed local tree may retain the checksum-manifest hold because hosted-only publication/workflow files are not byte-identical locally; the hosted repository remains the authoritative checksum gate.
- `revalidate_v0201_consistency.py` and the manual-script harnesses load both state controllers plus all three UI controllers before `app.js`.
- `revalidate_pptx_three_eras.py` passes 18/18 compatibility and round-trip checks.
- Cross-workspace isolation and transactional-open browser regressions pass with zero Presentations page errors.
- Launch/offline validation passes static-asset and restricted-API/touch-emulation checks; local HTTP/file navigation can be reported as not performed when blocked by the execution environment.
- The dedicated `revalidate_presentations_controls.py` remains the hosted behavior gate for Format-panel open/hide/reopen, formatting changes, selection clear/reselect, Undo/Redo restoration, compact drawer state and Escape handling. Slideshow behavior now runs independently in `revalidate_presentations_slideshow.py`; local HTTP navigation was blocked by the execution environment, so these browser paths are not claimed locally.
- Firefox, native WebKit/Safari, iPadOS, Edge and installed-PWA behavior remain explicit matrix/manual checks; unavailable engines are never inferred from Chromium results.

## v0.20.2.14 shared document-session decomposition

- `tests/test_document_session_modularization.py` requires document-session behavior to live in the focused shared UI controller and keeps both the controller and Office shell under the normal source-size ceiling.
- `tests/test_home_session_refinement.py` requires `shared/office-shell.js` to load/compose the controller rather than reimplement filename, dirty-state or download behavior.
- `service-worker.js` precaches `shared/ui/document-session-controller.js` so installed/offline workspaces keep the same shared session contract.
- The browser runner remains at 17 isolated scenarios; existing functional-correction coverage continues to exercise the shared title/session path rather than creating a redundant new browser harness.

## v0.20.2.13 PDF save decomposition

- `tests/test_pdf_save_modularization.py` enforces the new I/O boundary and the removal of PDF `app.js` from inherited architecture debt.
- `tests/browser/revalidate_pdf_save.py` is an isolated 17th Chromium scenario for both unified-save modes and download/button lifecycle.
- Existing PDF rendering, navigation and review scenarios remain separate release blockers.

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

Run `python3 scripts/check_architecture_guardrails.py`. The release runner now
executes this gate after the source audit and before unit/package tests. The
gate is intentionally ratcheted: inherited debt can shrink, but new debt or
cross-workspace coupling fails validation.


## v0.20.2.13 Presentations architecture consolidation

- `tests/test_presentations_modularization.py` requires the PPTX write adapter plus file/recovery controllers to load before `app.js`, remain within new-source limits and be precached offline.
- Package-preserving imported-slide mutation, notes patching, transition patching and new object XML generation now live in `io/pptx-write-adapter.js`.
- `tests/test_pptx_roundtrip_preservation.py` verifies that source-order preservation follows the writer boundary rather than requiring the implementation to remain in `app.js`.
- Manual-script browser harnesses load the writer before `file-controller.js` and before the editor entry point.
- Existing three-era PPTX, cross-workspace, transactional-open, recovery, controls and slideshow regressions remain release-blocking.

## v0.20.2.7 update-flow hardening

- `--dry-run` now validates a disposable candidate repository instead of only printing a plan; tests prove both success and validation failure leave the source checkout untouched.
- `scripts/update_checksums_incrementally.py` preserves all undeclared checksum entries and updates/removes only explicitly named patch paths.
- Slideshow behavior moved out of the broad Presentations control harness into `tests/browser/revalidate_presentations_slideshow.py`, giving it a fresh process/context and explicit tab state.
- The hosted Chromium regression runner now has thirteen independent scripts.
- Package SHA-256 is included in the updater report as an additional identity check.

## v0.20.2.6 Presentations decomposition

- `tests/test_presentations_modularization.py` verifies selection/history, Inspector, thumbnails, presenter notes and slideshow as focused components loaded before `app.js`, within new-source limits and precached offline.
- The Presentations `app.js` ratchet is 783 physical lines / 82 long lines; presentation-mode lifecycle and Fullscreen handling may not be reimplemented in the entry point.
- Browser harnesses that strip HTML script tags explicitly load the slideshow controller after the state/UI controllers and before `app.js`.
- `tests/browser/revalidate_presentations_slideshow.py` independently proves top/View/Present entry points, current/start behavior, slide counter navigation, Home/End/Arrow keys, Escape and the visible Exit control while remaining independent of headless Fullscreen API policy.
- Existing PPTX, recovery, cross-workspace and transactional-open browser regressions must remain unchanged.


- Browser validation now contains 14 isolated regression scripts, including a dedicated PDF page-rendering/navigation gate.
