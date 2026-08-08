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
### v0.20.2.15 — Shared workspace panel decomposition

Documents navigation-panel state, Presentations thumbnails/Format/notes panel state, PDF navigation-sidebar state and Spreadsheet layout markers move into `shared/ui/workspace-panel-controller.js`. `workspace-layout.js` remains the Documents ruler owner and delegates panel state to the new controller. No visible default or interaction is intentionally changed.

The next shared-UI cut should stay bounded and should not mix Documents ruler extraction with unrelated workspace behavior.

### v0.20.2.16 — Documents ruler model decomposition

Pure ruler math/state moves from `workspace-layout.js` to `shared/ui/document-ruler-model.js`: tick generation, active-page metrics, selected-block indent state, clamping, pointer conversion and indent application. DOM synchronization, observer wiring and pointer-drag interaction stay in `workspace-layout.js`. The external ruler-helper API remains compatible and no visible ruler behavior is intentionally changed.

The next shared-UI cut should keep the same boundary discipline: do not combine ruler interaction extraction with unrelated Documents or Spreadsheet behavior.

### v0.20.2.17 — Documents ruler interaction decomposition

Pointer-drag lifecycle moves from `workspace-layout.js` to `shared/ui/document-ruler-drag-controller.js`: pointer capture, pointerdown/move/up/cancel handling, drag-state transitions and indentation-application orchestration. Ruler DOM synchronization, rendering and observers stay in `workspace-layout.js`, while pure geometry remains in `document-ruler-model.js`. No visible ruler behavior is intentionally changed.

The next shared-UI cut should finish the remaining ruler DOM synchronization/observer debt or stop shared-UI decomposition if the resulting boundary would become less clear.

### v0.20.2.18 — Shared workspace contract consolidation

Workspace module detection, session-backed panel preference resolution and the `inkdesk:workspace-layout-ready` notification move into the existing `workspace-panel-controller.js`. `workspace-layout.js` retains the Documents ruler DOM synchronization/observer boundary and keeps its compatibility helper API through delegation. The file is now below 500 physical lines and its grandfathered debt entry is retired.

This closes the current shared workspace-layout debt cycle. Further decomposition should be driven by a concrete maintenance or regression need rather than line count alone.

### v0.20.2.19 — TXT editor interaction decomposition

TXT snapshot-history/Undo/Redo ownership moves to `apps/txt/history-controller.js`; Find bar/search interaction moves to `apps/txt/find-controller.js`. File lifecycle, encoding, line-ending preservation, Save, counts, wrap and text-size behavior remain in `app.js`. This bounded workspace cleanup retires the inherited TXT app.js line-count debt without changing the visible editor.

After this gate, only high-value cleanup should remain in 0.20.2.x. Do not chase every grandfathered file solely to reach zero debt; the transition to 0.20.3 should be based on behavioral stability and a frozen ownership map.

### v0.20.2.20 — Spreadsheet formula model decomposition

The immutable function catalog plus pure formula-session helpers now live in
`apps/spreadsheets/formula-model.js`: column/cell encoding, parenthesis tracking,
formula balancing, suggestion matching/insertion and the predicates that decide
reference selection, successive range insertion and commit completeness.
`formula-editor.js` keeps DOM/caret handling, persistent drafts, suggestion UI,
keyboard behavior and integration with the reference controller. Its existing
`InkDeskFormulaEditor` public helper surface is preserved by delegation.

This is intentionally the low-risk first Spreadsheet cut: pure deterministic
logic is independently testable before the remaining stateful editor session is
split. No cell-editing, formula, selection, Save or visual behavior changes.


### v0.20.2.21 — Spreadsheet formula session lifecycle decomposition

Persistent formula draft state moves from `formula-editor.js` to `apps/spreadsheets/formula-session.js`. The new module owns draft storage and the start/update/suspend/resume/commit/cancel state transitions without depending on the DOM. The editor remains responsible for caret/DOM synchronization, suggestions, keyboard routing and reference-controller integration.

This is a stability-driven cut rather than a line-count exercise: formula drafts can now be regression-tested as deterministic state transitions before the remaining suggestion/interaction UI is considered for a later bounded extraction.
