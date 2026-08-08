# InkDesk 0.20.2 — Data Safety and Browser Matrix

InkDesk 0.20.2 is a focused data-safety release. It does not add editing tools.

## Local recovery

Documents, Spreadsheets and Presentations now keep bounded recovery snapshots in IndexedDB after unsaved edits. On a later launch, the user can restore the latest private snapshot, open normally without deleting it, or discard it. The original selected file is never overwritten.

Retention is intentionally limited to three snapshots per document, twelve per workspace and thirty days. A confirmed copy download clears the active document recovery data.

## Browser validation

The standard incremental-update validation remains Chromium-only so workflow duration stays predictable. The repository also includes an explicit matrix runner for installed Playwright Chromium, Firefox and WebKit binaries. Strict mode can require every requested engine.

The incremental updater no longer repeats unit, audit and repository gates before calling the complete release validator. Full package validation now uses one release-validation pass.

Versioned application-shell URLs such as `module-registry.js?v=0.20.2` are canonicalized to their pre-cached shell entries before offline fallback, making the hosted offline check deterministic instead of depending on the browser HTTP cache.

## Scope

- No new editing features.
- No workflow-file changes in the update package.
- PDF, TXT and EPUB behavior is unchanged.
## Correction revision 2 — functional controls

- Fixes the Presentations format panel on compact/iPad-width layouts. The View control now opens a real side drawer instead of being permanently suppressed by the legacy responsive CSS rule.
- The format-panel button now reports `aria-expanded`, works independently on desktop and compact layouts, and Escape closes the compact drawer.
- Recovery validation no longer conflates IndexedDB recovery with whether presenter notes happen to be visible; presenter-notes visibility is checked separately by the control regression.
- Adds `revalidate_presentations_controls.py`, which behaviorally checks format-panel hide/show, object formatting, presenter-notes hide/show, thumbnails, responsive drawer behavior, and tab wiring.
- Adds a persistent functional acceptance matrix. The current tree inventories 210 visible interactive controls; controls without dedicated behavioral proof are explicitly marked scheduled rather than assumed working.

### Correction revision 3 — Presentations format panel cascade

- Removed the inherited compact `display:none` rule for the Presentations inspector.
- Added a final, presentation-scoped cascade guard in `shared/office-shell.css`, which loads after the product stylesheet.
- Desktop format-panel visibility and compact fixed-drawer behavior are now asserted with computed-style diagnostics in the browser regression.



#### Presentations control acceptance correction 4

The Format panel and Presenter Notes now have an explicit closed-at-open contract. The browser regression starts from that state and must prove that the visible View controls open, hide, and reopen the Format panel, that format controls mutate a selected object, and that Presenter Notes toggle reversibly. This prevents a correct collapsed startup state from being mistaken for a broken panel while still catching an unresponsive button.


### Correction revision 5 — deterministic Format-panel state

A deeper review found that the compact/iPad cold-start path could re-add the desktop `hide-inspector` class after the initial responsive synchronization. Because the compact drawer and desktop panel previously used separate CSS classes as state, the visible panel, button label and `aria-expanded` value could disagree. Presentations now uses one `inspectorOpen` boolean and derives the desktop/compact classes from it. Breakpoint changes are reconciled by both `matchMedia` and a resize fallback, and crossing the breakpoint closes the panel intentionally to keep state deterministic. The browser regression now includes a fresh 820 px context, reproducing the real compact cold-start path before accepting the Format button.

The correction also adds a repository-level DOM contract test for duplicate ids and unresolved direct app control references across all six workspaces.


### Correction revision 6 — Presentations responsive state simplification

- Removed breakpoint-driven JavaScript state mutation for the Format panel.
- `inspectorOpen` now always derives the same `inspector-open` / `hide-inspector` classes, regardless of viewport width.
- Resizing and rotation are CSS-only layout changes, so the panel, button label and `aria-expanded` cannot diverge while waiting for a media-query/animation-frame callback.
- Browser acceptance now verifies desktop open -> compact open continuity, compact close/reopen, Escape close, and fresh compact cold-start behavior.
