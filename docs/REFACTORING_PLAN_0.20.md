# Refactoring plan for the 0.20 line

InkDOS v0.20.0 consolidates the working beta without rewriting mature runtime
paths during the release transition. Two inherited files remain above the
repository's preferred 1,000-line source limit and have explicit extraction
plans.

## `apps/pdf/app.js`

Current responsibilities include document lifecycle, PDF.js rendering, page
windowing, text and form layers, review tools, navigation, bookmarks, comments,
fullscreen behavior, and Save orchestration.

Planned 0.20.x extraction order:

1. `pdf-renderer.js` — page cache, canvas, text layer, and form layer.
2. `pdf-review-model.js` — annotations, bookmarks, comments, and persistence.
3. `pdf-navigation.js` — outline, thumbnails, page and zoom state.
4. `pdf-controller.js` — small composition layer and workspace events.

Each extraction must preserve the permanent PDF.js architecture checks and pass
all PDF selection, form, review, Save, and memory-window regression tests.

## `shared/ui/workspace-layout.js`

This compatibility adapter currently normalizes several independently evolved
workspace layouts.

Planned 0.20.x extraction order:

1. Common panel and status helpers.
2. Documents layout adapter.
3. Spreadsheet layout adapter.
4. Presentations layout adapter.
5. PDF layout adapter.

The shared public event and data-attribute contract must remain compatible
during extraction. No visual redesign is part of these refactoring tasks.

## Guardrail phase added in v0.20.2.2

Before the extractions above begin, `AGENTS.md`, `architecture-policy.json` and
`scripts/check_architecture_guardrails.py` establish a zero-regression
refactoring contract. The ordered implementation sequence is now documented in
`docs/REFACTORING_SEQUENCE_0.20.md`. Presentations is intentionally the first
runtime decomposition target, followed by PDF and then shared UI.
