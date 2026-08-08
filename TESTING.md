## v0.20.2.20 Spreadsheet formula model decomposition

The v0.20.2.20 gate keeps the complete suite and the existing 17 Chromium scripts, and adds a deterministic model boundary for Spreadsheet formula syntax. The new tests require `formula-model.js` to load before formula reference/editor interaction, remain below the normal 500-line ceiling, preserve the existing `InkDeskFormulaEditor` helper surface, and pass edge cases for quoted parentheses, formula balancing, suggestion insertion and reference-selection predicates.

Local reconstruction result: **280/281 unit/package tests pass**; the only local hold is the authoritative full checksum test because the three publication-vendored PDF.js files are not present byte-for-byte in this reconstruction. Spreadsheet-specific Chromium regressions for XLSX, XLS zero display and formula-standby selection pass; the hosted workflow remains the final 17/17 gate.


The hosted package gate must preserve the complete behavior suite and verify that workspace module detection, session preference resolution and layout-ready notification are owned by `shared/ui/workspace-panel-controller.js`, while `shared/ui/workspace-layout.js` stays below 500 lines and retains its compatibility delegates. Expected unit/package count: 271. Expected Chromium regression count: 17/17.

## v0.20.2.14 shared document-session decomposition

- `tests/test_document_session_modularization.py` enforces the new shared UI ownership boundary, offline precache registration and Office-shell debt retirement.
- `tests/test_home_session_refinement.py` now follows title/download behavior into the extracted controller while requiring `shared/office-shell.js` to remain composition-only.
- The existing `tests/browser/revalidate_v02021_functional_corrections.py` remains the behavioral title/session gate for Spreadsheets and Presentations; the complete runner remains at 17 isolated Chromium scenarios.
- `shared/office-shell.js` is 315 physical lines and no longer needs an inherited-debt exemption; the new controller is below the normal 500-line ceiling.

## v0.20.2.13 PDF save decomposition

- `tests/test_pdf_save_modularization.py` requires the save controller to own both save paths, remain below normal source limits, load before `app.js` and be precached offline.
- `tests/test_pdf_unified_save.py` continues to enforce the single visible Save contract and now follows the save-controller boundary.
- `tests/browser/revalidate_pdf_save.py` independently exercises the PDF.js save path and the flattened annotated path, validates the downloaded PDF copies and verifies Save-button busy/available state.
- The hosted Chromium regression runner now has seventeen independent scripts; rendering, navigation, review and save are separate PDF scenarios.
- `apps/pdf/app.js` is below 500 physical lines and no longer has an inherited-debt exemption.


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

- Architecture guardrails now include the dedicated PDF page-renderer, navigation and review controllers. The PDF `app.js` ratchet is reduced again after navigation/sidebar extraction; both new viewer controllers remain below the 500-line new-file ceiling.
- The Python suite contains 252 tests. The hosted repository remains the authoritative full checksum gate because the reconstructed local tree does not contain the three pinned PDF.js publication files byte-for-byte.
- `revalidate_v0201_consistency.py` and the manual-script harnesses load both state controllers plus all three UI controllers before `app.js`.
- `revalidate_pptx_three_eras.py` passes 18/18 compatibility and round-trip checks.
- Cross-workspace isolation and transactional-open browser regressions pass with zero Presentations page errors.
- Launch/offline validation passes static-asset and restricted-API/touch-emulation checks; local HTTP/file navigation can be reported as not performed when blocked by the execution environment.
- The dedicated `revalidate_presentations_controls.py` remains the hosted behavior gate for Format-panel open/hide/reopen, formatting changes, selection clear/reselect, Undo/Redo restoration, compact drawer state and Escape handling. Slideshow behavior now runs independently in `revalidate_presentations_slideshow.py`; local HTTP navigation was blocked by the execution environment, so these browser paths are not claimed locally.
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

Run `python3 scripts/check_architecture_guardrails.py`. The release runner now
executes this gate after the source audit and before unit/package tests. The
gate is intentionally ratcheted: inherited debt can shrink, but new debt or
cross-workspace coupling fails validation.


## v0.20.2.10 Presentations architecture consolidation

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
