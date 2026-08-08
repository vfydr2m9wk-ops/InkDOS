# InkDesk v0.20.2.23 — Spreadsheet Formula Recovery Hardening

This maintenance release closes the remaining gap between Spreadsheet formula drafts and InkDesk's private local-recovery system.

## Stability changes

- Pending Spreadsheet formula drafts are now serialized into IndexedDB recovery snapshots instead of existing only in the live page session.
- Restoring a workbook restores those drafts as resumable per-cell drafts without committing them silently into the workbook model.
- Formula start, update, suspend, resume, commit, cancel and restore transitions now notify the recovery boundary so snapshot scheduling follows actual unsaved state.
- Cancelling the only pending formula draft clears obsolete recovery snapshots while preserving the original-file source record needed for future recovery.
- Confirmed New/Open replacement discards recovery state for the previous workbook only after a replacement XLS/XLSX has parsed successfully.
- Local recovery writes are fenced by a document-generation token. An in-flight snapshot from an older document cannot be written under a newer document identity.
- Recovery cleanup waits for any in-flight write before deleting snapshots/source state, closing a race that could recreate stale recovery data after Save/discard.

## Scope

No formula syntax, grid selection, workbook serialization, visual layout or GitHub workflow behavior is intentionally changed. The release adds deterministic formula-recovery tests and extends the existing local-recovery Chromium regression rather than adding another browser script.
