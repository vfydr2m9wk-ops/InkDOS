# InkDesk v0.20.2.27 — Recovery Source Rehydration and Metadata Continuity Hardening

This maintenance release hardens private local recovery across tabs and repairs release-metadata drift detected after v0.20.2.26.

## What changed

- The local-recovery manager keeps the active source package in memory for the lifetime of the editing session.
- Before writing a new recovery snapshot, an imported DOCX/XLS(X)/PPTX source package is rehydrated into IndexedDB if it was removed by cleanup, eviction or an older InkDesk session.
- Fresh source packages without snapshots receive a grace period instead of being treated immediately as abandoned by another tab.
- Snapshot-only cleanup now defers when new edits arrive while cleanup is waiting for an in-flight write, and immediately replaces a snapshot if an edit races with deletion.
- Save cleanup uses the same post-cleanup safety rule, reducing the window where a new edit could exist without recovery evidence.
- Restored sessions retain the recovered source package in memory, so subsequent edits can rebuild the source record if needed.
- `README.md`, root `RELEASE_NOTES.md`, `CHANGELOG.md` and the release-history index are synchronized to the actual current version.
- A permanent metadata-consistency test now fails if the public release entry points drift behind `VERSION.json`.

## Stability rationale

A clean imported document can legitimately keep its source package even when no recovery snapshot exists yet. Previously, opening another tab could classify that source as orphaned immediately. If the original tab later resumed editing, a subsequent recovery could lose the preservation-aware source context. v0.20.2.27 makes source continuity resilient to this cross-tab lifecycle and to source-store loss before the next snapshot.

## Scope

No visual layout, formula syntax, workbook calculation, document editing command or file-format feature is intentionally changed.

## Validation target

The hosted release gate remains the authoritative full unit/checksum suite plus **17/17 Chromium regression scripts**.
