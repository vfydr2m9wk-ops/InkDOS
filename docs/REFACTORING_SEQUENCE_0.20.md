# Refactoring sequence for the InkDesk 0.20 line

The sequence is intentionally incremental. One behavior-neutral extraction must
pass the full release gate before the next ownership boundary is moved.

| Release | Scope | Runtime behavior change |
| --- | --- | --- |
| 0.20.2.2 | Guardrails, policy, architecture checks and AI instructions | None |
| 0.20.2.3 | Presentations: Format/Inspector extraction | None intended |
| 0.20.2.4 | Presentations: thumbnails and presenter-notes extraction | None intended |
| 0.20.2.5 | Presentations: state/history/selection extraction | None intended |
| 0.20.2.6 | Presentations: slideshow/presentation-mode extraction | None intended |
| 0.20.2.7 | Update-flow hardening: real dry-run, incremental checksums, isolated slideshow regression | None intended |
| 0.20.2.8 | Presentations: I/O/save/recovery extraction | None intended |
| 0.20.2.10–0.20.2.13 | PDF rendering, navigation, review and Save decomposition | None intended |
| 0.20.2.14+ | Shared UI decomposition, beginning with document-session behavior | None intended |
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
    history-controller.js
    selection-controller.js
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
    slideshow-controller.js
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

v0.20.2.5 implements the third boundary. `state/selection-controller.js` owns
selected-object identity, canvas clear/reselect behavior, drag/resize/rotate
interactions, selection handles and alignment guides.
`state/history-controller.js` owns snapshot capture, bounded Undo/Redo stacks,
action wrapping, restoration and toolbar disabled-state synchronization. The
entry point still owns the presentation document itself and composes these state
controllers with the previously extracted UI controllers.

v0.20.2.6 implements the fourth boundary.
`presentation/slideshow-controller.js` owns presentation-mode entry/exit,
from-start/from-current actions, keyboard and pointer navigation, presentation
counter/help state, slide fitting, transition animation and Fullscreen API
fallback handling. Transition editing and the presentation document remain in
`app.js`; the slideshow controller receives them through explicit dependencies.

v0.20.2.7 hardens the update path before the next runtime extraction. Dry-run now validates a disposable candidate tree, incremental checksum tooling preserves authoritative hosted-only hashes, and slideshow browser behavior runs in an isolated process/context. No editor runtime responsibility moves in this step.

v0.20.2.8 implements the fifth Presentations ownership boundary. `io/file-controller.js` owns PPTX open/save orchestration and imported-source buffers; `io/recovery-controller.js` owns recovery capture/restore and recovery-manager lifecycle. The entry point continues to own the active presentation model plus editing/format parsing helpers and composes both controllers through explicit callbacks.

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


## v0.20.2.10 — Presentations architecture consolidation

Final Presentations consolidation before beginning PDF decomposition. Package-preserving PPTX write/patch helpers move behind a dedicated I/O adapter; the visible editor and file-format contract remain frozen. After this gate is accepted, the next architectural target is PDF.


### v0.20.2.11 — PDF navigation decomposition

Page navigation, thumbnails, outline destinations, bookmark navigation and sidebar tab state move out of the PDF entry point. Review annotations and Save remain separate future cuts.

### v0.20.2.12 — PDF review decomposition

Review persistence, selected-text annotations, free marker/text overlays, comments and review Undo move behind focused PDF review components. Unified Save remains intentionally separate for the next bounded extraction.


### v0.20.2.14 — Shared document-session decomposition

The first shared-UI boundary moves filename normalization, editable-title state, dirty-state bridging, discard protection and download-name rewriting from `shared/office-shell.js` into `shared/ui/document-session-controller.js`. The Office shell remains responsible for loading/composition and preserves `InkDeskDocumentSessionReady`. No visible control or workspace behavior changes.

Next shared-UI cuts should remain similarly bounded; `shared/ui/workspace-layout.js` is still grandfathered and is the primary remaining shared UI debt target.
