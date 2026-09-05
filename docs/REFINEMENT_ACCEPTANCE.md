# InkDOS refinement acceptance matrix — checkpoint 2

Baseline: `1.0.0-beta.5`, sequence 62.
Checkpoint target: `1.0.0-beta.9`, sequence 63.

This checkpoint addresses the mobile Home gutter/theme regressions observed on-device and the Documents AppHome layout failure. PASS means direct evidence exists; PARCIAL means the remaining editor-wide phase still owns part of the criterion.

| # | Criterion | State | Evidence / scope |
|---:|---|---|---|
| 1 | Home has no visible giant app catalog | PASS | Active Home remains Recent-first. |
| 2 | Home is centered on Recent files | PASS | Recent remains the primary content. |
| 3 | Recent filters remain usable | PASS | Registry-derived All + six app filters; horizontal strip retained. |
| 4 | Clear Recent disappears when empty | PASS | Existing empty/populated/clear behavior retained. |
| 5 | Global Open/Create do not dominate Home | PASS | Only discreet empty-state Open remains. |
| 6 | Real grid app launcher exists | PASS | Registry-derived six-app launcher retained. |
| 7 | Launcher and Settings are separate | PASS | Separate shared surfaces retained. |
| 8 | Theme is global | PARCIAL | Home/suite/shared-shell token bridge is unified in this checkpoint; editor-wide token unification remains Phase 7. |
| 9 | No cramped native theme select in active UI | PASS | Shared Settings radio choices retained. |
| 10 | Launcher is available in apps | PASS | Shared trigger retained in all six apps. |
| 11 | Mobile AppHome is a normal page | PASS | Shared AppHome is now a dedicated viewport-level startup surface with its own scroll, independent of editor grids. |
| 12 | Desktop AppHome uses available width | PASS | The canonical host occupies the viewport; the inner page remains bounded to 1180 px on wide screens. |
| 13 | AppHome never exceeds viewport | PASS | One viewport-level AppHome contract is shared by all six apps; 320–1440 px plus 667×375 landscape passed the local Chromium matrix without horizontal overflow. |
| 14 | Editors never exceed viewport | NÃO TESTADO | Phase 6 editor matrix not yet completed. |
| 15 | Toolbars have dedicated mobile composition | NÃO TESTADO | Phase 6. |
| 16 | Long titles do not break toolbars | PARCIAL | Existing ellipsis behavior remains; full editor matrix is Phase 6. |
| 17 | File picker stays native/local | PASS | Existing native file inputs retained. |
| 18 | Apps limit file formats appropriately | PASS | Central registry contract retained. |
| 19 | Incompatible formats are handled without crash | PARCIAL | Phase 5 continuation. |
| 20 | Recent files route to correct module | PARCIAL | Phase 5 continuation. |
| 21 | Read-only apps do not invent creation | PASS | PDF/EPUB remain Open-only. |
| 22 | Bottom sheets respect safe area | PASS | Shared mobile sheets retain safe-area inset. |
| 23 | Dynamic viewport is used appropriately | PARCIAL | Shared surfaces use `dvh`; editor-wide verification remains Phase 6. |
| 24 | Institutional links do not occupy active mobile Home | PASS | Links remain in Settings. |
| 25 | No unnecessary duplicate navigation | PARCIAL | Shared roles are retained; final sanitization remains. |
| 26 | Desktop remains primary experience | PASS | No desktop editor composition is changed by this checkpoint. |
| 27 | Mobile is not merely compressed desktop | PARCIAL | Home/AppHome responsive treatment improved; editor toolbars remain Phase 6. |
| 28 | Dirty state is not discarded silently | PASS | Lifecycle/recovery behavior untouched. |
| 29 | Light/dark share structure | PARCIAL | Home now uses one canonical token bridge in both themes; editor-wide Phase 7 remains. |
| 30 | Application remains usable offline | PASS | No new runtime asset is introduced; existing precache continues to cover modified shared CSS. |

## Checkpoint 2 evidence before GitHub Actions

- On-device report identified mixed light/dark controls and insufficient horizontal gutter on the beta.5 Home.
- Source inspection confirmed `refinement-home.css` overrode the original bounded Home width and mixed canonical theme tokens with inherited `--muted`/`--edge`/suite tokens.
- Source inspection confirmed Documents AppHome remained inside the two-column editor workspace while the sidebar was hidden; legacy `.welcome-card` `!important` rules also overrode the shared AppHome host.
- Local Chromium composition probe after the fix measured the Documents AppHome host/viewport at 390 CSS px in a 390 px viewport, with a single workspace grid column and visible Create/Open/Recent content.
- Local Chromium dark-theme probe measured a 20 px mobile content gutter and explicit light text on dark `Open file` and suite controls.
- Full repository unit/browser/release validation is **NÃO TESTADO** for beta.6 until the package runs through GitHub Actions.
- Beta.6 gate evidence: 380/380 unit/package tests PASS and 26/27 Chromium regression scripts PASS. The sole blocker was the Home `Open file` contrast assertion; no commit/push occurred. The follow-up keeps criterion 29 PARCIAL while adding explicit resolved-theme contrast pairs without changing layout or the 4.5:1 acceptance threshold.

- Beta.6 follow-up gate (2026-09-05): the inline resolved-theme synchronizer still failed the immediate Home contrast assertion in Actions because MutationObserver delivery occurs after `applyTheme()` returns. The transaction rolled back and `main` remained unchanged.
- Beta.6 r2 keeps the 4.5:1 assertion unchanged and makes the normal `InkDOSAppShell.applyTheme()` path dispatch `inkdos:theme-changed` synchronously; `shared/suite-shell.js` consumes that event immediately while retaining the MutationObserver as a fallback for direct DOM attribute changes. Targeted Chromium verification measured 13.25:1 in dark and 15.15:1 in light. Full GitHub Actions validation remains pending.

- Beta.6 component-reuse revision (2026-09-05): after the synchronous event variant again failed the same `Open file` contrast assertion in Actions, the bespoke theme synchronization path was removed. Home `Open file` now uses the already-established `.suite-action` component, so its foreground/background/border states come from the same suite theme tokens as other passing buttons. The 4.5:1 acceptance assertion is unchanged; the regression additionally requires `.suite-action` reuse and forbids an inline style override on this control. Full GitHub Actions validation of this revision remains pending.

- Beta.6 primary-component revision (2026-09-05): the neutral `.suite-action` reuse still exposed a cascade conflict in Actions (`#f2f4f7` text on white, 1.10:1). Home `Open file` now uses the canonical `.suite-action.primary` variant, matching the suite Open action instead of adding another Home-specific color rule. The WCAG 4.5:1 computed-color gate remains unchanged and the browser contract now requires the primary component class. Full GitHub Actions validation remains pending.


- Beta.6 canonical-shell revision (2026-09-05): the repeated Apps/Settings contrast failure was isolated to CSS transition timing rather than unresolved theme tokens. The Home now discards the legacy `.suite-menu` trigger and delegates creation to the existing `InkDOSAppShell.refreshTriggers()` path, yielding the same `.inkdos-global-trigger` controls owned by the shared shell. The component's theme-sensitive background/color are non-animated, making the immediate WCAG contrast measurement deterministic. Targeted Chromium evidence: Apps and Settings both resolve immediately to `rgb(242, 244, 247)` on `rgb(36, 41, 50)` in dark mode, and both are free of the `.suite-menu` class. The 4.5:1 gate is unchanged.


## Checkpoint 2 architecture closure — AppHome

- GitHub Actions run #34 (`a4764ce0abbaeabf50071e0f6dd5939759eda531`) confirmed that the earlier Home fixes now pass: repository validation, source audit, architecture guardrails and 380/380 unit/package tests passed; 26/27 browser scripts passed. `revalidate_refinement_checkpoint.py` advanced past Home dark background, Open file, Apps and Settings and failed later on the Documents AppHome width assertion. The transaction correctly rolled back before commit/push.
- Full-source review identified the common cause: each AppHome was embedded inside an editor-specific layout container. Documents in particular inherited the editor `#viewport` padding/grid, so startup width depended on editor CSS and required brittle per-editor escape rules.
- The startup architecture is replaced rather than patched: `shared/app-home.js` promotes the existing `[data-app-home]` host to a direct child of `document.body`; `shared/ui/app-home.css` owns it as `position:fixed; inset:0; width:100vw; height:100dvh; overflow:auto`. Editor sidebars, grids, toolbars and viewport padding no longer participate in AppHome geometry.
- The old Documents-only CSS escape (`workspace` forced to one column and `viewport` forced across the grid) is removed. The regression now asserts the architecture itself: direct `body` parent, fixed positioning, full viewport width, no horizontal overflow and correct Create/Open capability counts for all six apps.
- Local Chromium matrix after the replacement: Documents, Spreadsheets, Presentations, PDF, TXT and EPUB each matched viewport widths 320, 360, 375, 390, 412, 430, 768, 1024, 1280 and 1440 px; all also passed 667×375 landscape. PDF/EPUB remained Open-only; the other four retained Create + Open; launcher retained six modules.
- The Home assertions already proven by run #34 are not weakened or redesigned by this change. Final promotion to `main` still depends on the independent GitHub Actions full gate.
