# InkDOS refinement worklog — checkpoint 2

## Baseline

- Source package: `1.0.0-beta.5`.
- Source sequence: `62`.
- Source state was confirmed `complete` before this checkpoint.

## Changes in checkpoint 2

- `shared/ui/refinement-home.css`: added a canonical theme bridge so Home, suite controls and shared shell consume the same background/surface/text/muted/border/hover/selected state; dark mode now maps inherited `--surface-soft`, `--muted` and `--edge` to the dark palette.
- `shared/ui/refinement-home.css`: added 20 px mobile inline gutter with safe-area support and retained an intentional horizontally scrollable Recent filter strip.
- `shared/ui/refinement-home.css`: made Recent filter/Open button and topbar suite controls consume canonical theme tokens explicitly.
- `shared/ui/app-home.css`: strengthened the shared AppHome host reset against legacy app-specific `!important` card styles.
- `shared/ui/app-home.css`: collapsed the Documents startup workspace to one column while AppHome is active and forced the viewport into that column, removing the blank/narrow startup composition.
- `tests/browser/revalidate_refinement_checkpoint.py`: now loads each page's actual linked styles, checks dark/light Home contrast, mobile gutter, mandatory Home widths, all six AppHomes across the width matrix plus landscape, and Documents full-width startup geometry.
- `tests/test_refinement_checkpoint.py`: added static contracts for the theme/gutter bridge and Documents grid escape.

## Local evidence

- Minimal Documents composition Chromium probe: AppHome visible; `.workspace` one 390 px column; `#viewport` 390 px; AppHome host 390 px at viewport 390x844.
- Minimal Home dark-theme Chromium probe: Recent content left/right gutter 20 px; body gradient resolves to the dark palette; `Open file` and suite controls resolve to `rgb(242, 244, 247)` text on `rgb(36, 41, 50)` surfaces.
- Python syntax compilation for the modified browser/unit regression files: PASS.
- Full repository validation: NOT TESTED locally because this environment does not contain a literal current checkout and blocks GitHub/local browser navigation.
- GitHub Actions beta.6/sequence 63 candidate gate: repository validation PASS, source audit PASS, architecture guardrails PASS, unit/package tests 380/380 PASS, browser regressions 26/27 PASS. The only failure was `revalidate_refinement_checkpoint.py` at the WCAG contrast assertion for Home `Open file`; transaction rolled back before commit/push.
- Follow-up contrast fix: Home `Open file` and topbar suite controls now receive explicit foreground/background pairs from `data-resolved-theme` (dark `#f2f4f7` on `#242932`; light `#202633` on `#fff`) with WebKit text fill pinned to the same foreground. The regression threshold remains 4.5:1 and now reports computed colors/ratio on failure.
- Actions follow-up: the stylesheet-only guard still resolved `Open file` as `rgb(242, 244, 247)` on `rgb(255, 255, 255)`. `shared/suite-shell.js` now synchronizes the resolved-theme pair directly onto Home controls with inline `important` declarations and observes subsequent theme changes, removing native/button cascade ambiguity.

- Actions follow-up 2: the element-level MutationObserver synchronizer still raced the immediate contrast assertion (`rgb(242, 244, 247)` on `rgb(255, 255, 255)`, ratio 1.10). The candidate rolled back before commit/push.
- Beta.6 r2: `shared/app-shell.js` now emits a synchronous `inkdos:theme-changed` event from `applyTheme()` via a manifest text replacement; `shared/suite-shell.js` listens synchronously and keeps the MutationObserver only as a fallback. The acceptance threshold/test is unchanged. A targeted Chromium harness measured dark 13.25:1 and light 15.15:1; full Actions gate is pending.

- Actions follow-up 3 (component reuse): the synchronous theme-event variant still failed the same immediate `Open file` contrast assertion in GitHub Actions (26/27 browser scripts PASS; computed `rgb(242, 244, 247)` on `rgb(255, 255, 255)`, ratio 1.10). Instead of adding another element-level theme exception, `Open file` now reuses the existing canonical `.suite-action` button component. The dedicated inline synchronizer, MutationObserver hook, WebKit text-fill override, and Home-specific light/dark contrast guard were removed. `recent-open` now carries layout only. The existing 4.5:1 browser gate remains unchanged and now also asserts that the control has the `.suite-action` class and no inline style override.

- Actions follow-up 4 (primary component reuse): GitHub Actions confirmed that the neutral `.suite-action` still inherited a white background in the Home cascade while its text resolved to the dark palette (26/27 browser scripts PASS; 1.10:1). `Open file` now reuses the already-established `.suite-action.primary` variant used by the original suite Open action. This gives the control the canonical suite accent background and white foreground in both themes, removes dependence on the contaminated neutral surface token, and keeps the 4.5:1 computed-color assertion unchanged. Full Actions validation remains pending.


- Actions/root-cause resolution (canonical shell reuse): repeated menu contrast failures were traced to the generic `background-color .12s` button transition. The theme tokens were already resolving to the correct dark values, but the regression reads computed contrast immediately after `applyTheme()`, while the button was still interpolating from the light surface. Home no longer repurposes the legacy `.suite-menu`: `shared/suite-shell.js` removes that control, marks `.hub-topbar` as the canonical titlebar region, and delegates Apps/Settings creation to `InkDOSAppShell.refreshTriggers()`. Both controls are now the existing `icon-btn inkdos-global-trigger` component produced by `shared/app-shell.js`. `shared/ui/app-shell.css` excludes background/color from transitions for this component so theme contrast changes atomically. A targeted Chromium probe on the reconstructed beta.5 Home measured immediate dark `rgb(242, 244, 247)` on `rgb(36, 41, 50)` for both Apps and Settings; neither control carries `.suite-menu`.


## Architecture replacement after Actions run #34

Run #34 proved that the prior Home/theme work is no longer the blocker: 380/380 unit/package tests passed and 26/27 browser scripts passed. The refinement browser script advanced to its AppHome geometry section and failed the Documents 390 px full-width assertion.

A full review of the startup path found that the shared AppHome was still physically nested inside each editor's legacy layout. In Documents, `workspace-layout.css` deliberately applies editor padding/grid rules to `#viewport`; because the startup host lived inside that viewport, the shared AppHome had to fight editor geometry through increasingly specific overrides. This was the source of the repeated width/cascade failures.

The problematic path is replaced, not patched:

- `shared/app-home.js` promotes the existing `[data-app-home]` element to `document.body` before rendering the shared startup UI. Existing IDs and native file inputs remain unchanged, so app actions continue to activate the original create/open controls.
- `shared/ui/app-home.css` defines one viewport-level startup surface for all six apps (`fixed`, `inset:0`, `100vw`, `100dvh`, own scrolling).
- All editor-specific AppHome escape rules that hid/reflowed toolbars, sidebars, workspaces and viewports are removed from this shared stylesheet.
- `tests/browser/revalidate_refinement_checkpoint.py` now verifies the architectural invariant across all six apps instead of requiring the obsolete Documents one-column editor workaround.
- `tests/test_refinement_checkpoint.py` statically prevents reintroduction of the old Documents workspace/grid escape.

Local Chromium coverage for the replacement exercised all six AppHomes at 320/360/375/390/412/430/768/1024/1280/1440 px and 667×375 landscape. Every host occupied the full viewport without document-level horizontal overflow; Create/Open capability counts and the six-module launcher remained correct. This targeted matrix covers the entire portion of `revalidate_refinement_checkpoint.py` that had not executed successfully in run #34.
