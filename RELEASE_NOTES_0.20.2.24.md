# InkDesk v0.20.2.24 — Spreadsheet History Safety Hardening

This maintenance release hardens Spreadsheet Undo/Redo at workbook boundaries and makes recovered sessions retain their usable history.

## Stability changes

- Undo/Redo actions are now tagged with the worksheet where the change originated, so invoking Undo from another tab cannot mutate the wrong worksheet.
- History restoration recalculates the workbook before repainting, preventing dependent formula displays from remaining stale after Undo/Redo.
- Pending formula drafts block Undo/Redo until the draft is confirmed or cancelled, avoiding changes to the workbook model underneath visible draft text.
- Spreadsheet recovery snapshots now include bounded Undo/Redo history and restore it together with the workbook state.
- The history controller is DOM-free, capped at 80 actions, clone-safe, and independently testable.
- Browser harnesses that inject Spreadsheet runtime scripts explicitly load the history controller before `app.js`.

## Scope

No formula syntax, XLS/XLSX serialization, workbook visual layout, sheet-tab behavior or GitHub workflow behavior is intentionally changed. This release is a data/state-integrity hardening patch.
