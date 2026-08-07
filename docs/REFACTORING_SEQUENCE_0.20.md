# Refactoring sequence for the InkDesk 0.20 line

The sequence is intentionally incremental. One area is stabilized before the
next large source file is decomposed.

| Release | Scope | Runtime behavior change |
| --- | --- | --- |
| 0.20.2.2 | Guardrails, policy, architecture checks and AI instructions | None |
| 0.20.2.3 | Presentations decomposition | None intended |
| 0.20.2.4 | PDF decomposition | None intended |
| 0.20.2.5 | Shared UI decomposition | None intended |
| 0.20.2.6 | Documents/Spreadsheets cleanup | None intended |
| 0.20.2.7 | Architecture consolidation and dead-code cleanup | None intended |
| 0.20.3 | Format fidelity work resumes | Explicitly scoped |

## First extraction target: Presentations

`apps/presentations/app.js` should gradually become an orchestration layer.
Candidate ownership boundaries are:

```text
apps/presentations/
  app.js
  state/
    presentation-state.js
    history.js
    selection.js
  ui/
    toolbar.js
    inspector.js
    thumbnails.js
    presenter-notes.js
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

## Second target: PDF

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
