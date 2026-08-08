# Persistent spreadsheet formula session

Development sequence `0.19.4.10` replaces the wide floating cell input from
`0.19.4.9` with a persistent draft session inside the real grid cell.

## Normal cell dimensions

A formula draft uses the selected cell's existing `contenteditable` surface.
The cell keeps its original row height and column width, clips long text, and
mirrors the complete formula in the formula bar.

## Drafts survive cell changes

An incomplete formula is stored by worksheet and cell reference for the current
page session. A user may type `=S` in C1, select A1 and enter a number, return to
C1, and continue the draft. Grid rerenders reapply the visible draft.

A click on another cell has two meanings:

- before the formula expects a reference, the draft is suspended and the new
  cell can be edited normally;
- after an operator or an open function parenthesis, the click becomes a formula
  reference without changing the target cell.

## Suggestions

Suggestions appear only after two function letters at a valid function boundary:

- `=`: no list;
- `=S`: no list;
- `=SU`: SUM suggestions;
- `=SUM(A`: no AVERAGE suggestion.

Tab or pointer click accepts a suggestion. Enter confirms the formula.

## References

After `=SUM(`, clicking A1 inserts A1. Clicking B1 next inserts `,B1` without
requiring Ctrl. Pointer dragging inserts a range such as `A1:A10`. Ctrl/Command
and the touch `+ Range` control remain available.

## Operators

The arithmetic engine supports `+`, `-`, `*`, `/`, `^`, parentheses, and
postfix percentage. `10%` evaluates to `0.1`; remainder remains available as
`MOD(number, divisor)`.

## v0.20.2.20 ownership boundary

The formula session is now split between deterministic syntax/model logic and
stateful editor interaction. `formula-model.js` owns the immutable function
catalog plus pure helpers for cell/reference encoding, parenthesis depth,
formula balancing, suggestion matching/insertion, reference-selection
eligibility and formula completeness. `formula-editor.js` owns the persistent
draft Map, active-cell state, DOM/caret synchronization, suggestion rendering,
keyboard handling and reference-controller integration.

`InkDeskFormulaEditor` continues to expose the same pure helper functions by
delegating to the model, so callers do not need to change. This boundary is
intended to make formula behavior independently testable before any later
stateful session extraction.


## v0.20.2.21 lifecycle boundary

Persistent draft storage and state transitions now live in `formula-session.js`. The module owns the draft Map and the active-session fields required to start, update, suspend, resume, prepare a commit, prepare a cancellation and clear the active target. `formula-editor.js` retains DOM/caret synchronization, suggestion UI, keyboard event routing and reference-controller integration.

The session module has no DOM dependency and is tested directly in Node. A suspended draft is keyed by worksheet and cell reference, resuming the same key restores its saved value/caret, commit removes the saved draft, and cancellation exposes the original display value before clearing the active target.

## v0.20.2.22 safety boundary

`formula-safety.js` now coordinates formula drafts with workbook lifecycle operations. A draft may remain in the editor/session without entering the workbook model, so Save must not claim success while such a draft is pending. New/Open and before-unload include the draft state in their unsaved-work checks, and a replacement workbook clears the draft session only after parsing succeeds. `formula-session.js` exposes deterministic `hasDrafts()` and `reset()` operations for this boundary.


## v0.20.2.23 recovery boundary

Formula drafts are serializable recovery state. `formula-session.js` exports normalized draft records keyed by worksheet/cell and imports them without activating or committing a cell. `formula-editor.js` reapplies restored drafts to the rendered grid and emits lifecycle notifications that allow the workbook recovery manager to schedule or clear snapshots.

The recovery payload uses schema version 2 and includes `formulaDrafts`. Restoring a snapshot reconstructs the workbook first and then reapplies pending formula drafts as suspended/resumable drafts. Confirmed workbook replacement discards the prior recovery record only after the replacement file parses successfully.

## v0.20.2.24 history safety boundary

Spreadsheet history is now workbook-scoped rather than implicitly bound to whichever worksheet is visible when Undo or Redo is requested. Each history action carries its originating worksheet index; applying the action targets that worksheet and recalculates the workbook before the visible grid is refreshed.

Pending formula drafts block history mutation until they are confirmed or cancelled, preventing Undo/Redo from changing the committed workbook underneath draft text that exists only in the formula session. Recovery payload schema version 3 also carries bounded Undo/Redo stacks, so a restored session retains its usable committed-edit history rather than reopening with empty history buttons.

## v0.20.2.25 post-save recovery continuity

Formula/history snapshots are only useful if restore can reconstruct the workbook against the correct source package. Save-copy cleanup therefore retains the active OOXML source while the editing session continues. If a later formula or cell edit creates a new recovery snapshot, Restore still has the original workbook package available and does not fall back to blank-package reconstruction.

## v0.20.2.26 export confirmation boundary

A generated XLSX download is not treated as proof that the user retained a saved file. Before dispatch, Spreadsheet recovery is flushed; after dispatch, committed dirty state and recovery snapshots remain intact. The user must verify the XLSX in the browser's Downloads before explicitly discarding or replacing the workbook. Formula drafts remain blocked from Save by the existing safety coordinator, so this boundary applies only after formula-session state has been committed or cancelled.

