# Refactoring sequence for the InkDesk 0.20 line

The sequence is intentionally incremental. One behavior-neutral extraction must
pass the full release gate before the next ownership boundary is moved.

| Release | Scope | Runtime behavior change |
| --- | --- | --- |
| 0.20.2.2 | Guardrails, policy, architecture checks and AI instructions | None |
| 0.20.2.3 | Presentations: Format/Inspector extraction | None intended |
| 0.20.2.4 | Presentations: thumbnails and presenter-notes extraction | None intended |
| next 0.20.2.x | Presentations: state/history/selection, then slideshow and I/O in bounded steps | None intended |
| later 0.20.2.x | PDF decomposition | None intended |
| later 0.20.2.x | Shared UI decomposition | None intended |
| later 0.20.2.x | Documents/Spreadsheets cleanup | None intended |
| final 0.20.2.x | Architecture consolidation and dead-code cleanup | None intended |
| 0.20.3 | Format fidelity work resumes | Explicitly scoped |

## Presentations decomposition

`apps/presentations/app.js` should gradually become an orchestration layer. The
current target ownership map is:

```text
apps/presentations/
  app.js
  state/
    presentation-state.js
    history.js
    selection.js
  ui/
    toolbar.js
    inspector-controller.js
    thumbnails-controller.js
    presenter-notes-controller.js
    dialogs.js
  editing/
    text-editing.js
    object-transform.js
    shapes.js
    images.js
    arrange.js
  presentation/
    slideshow.js
    transitions.js
  io/
    open-pptx.js
    save-pptx.js
    recovery-adapter.js
```

This is a target map, not permission to create empty files. A module is created
only when real behavior is extracted into it.

v0.20.2.3 implemented the first boundary: `ui/inspector-controller.js` owns the
Format-panel state and property controls while `app.js` supplies explicit
dependencies for selection, dirty state, rendering, relayout and history.

v0.20.2.4 implements the second boundary. `ui/thumbnails-controller.js` owns
thumbnail rendering and thumbnail panel visibility. `ui/presenter-notes-controller.js`
owns the presenter-notes editor state, character count, input debounce and notes
panel visibility. The visible UI and default open/closed state remain unchanged.

## Later target: PDF

The current PDF controller combines document lifecycle, PDF.js rendering,
windowed pages, navigation, forms, review annotations, bookmarks/comments,
fullscreen and Save orchestration. Extraction should separate rendering,
navigation, review state and file lifecycle without changing PDF capabilities.

## Shared UI

After workspace-specific state is clearer, split shared UI by stable concepts
such as title editing, zoom controls, panel state, dirty-state presentation and
recovery dialogs. Shared components must not become a dependency on a specific
workspace.

## Zero-regression rule

If an extraction causes a behavioral regression, refactoring stops at that
release until the regression is explained, fixed and permanently tested. Debt
from one extraction is not carried into the next module.
