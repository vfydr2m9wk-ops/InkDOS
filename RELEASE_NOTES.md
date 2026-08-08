# InkDesk v0.20.2.30 — Recovery Session Isolation Hardening

This maintenance release prevents one browser tab from deleting another tab's local recovery snapshots when both tabs work with the same Office file identity.

## Current release

- Recovery snapshots now carry a per-manager `sessionId` in addition to the existing document identity.
- `clearSnapshots()`, `markClean()`, `discardCurrent()` and `resetSnapshots` operate only on the current recovery session.
- The three-snapshot retention limit is applied per document session, so snapshots from another tab are not mixed into the current tab's rolling history.
- Restoring a recovery removes the recovered session's old snapshots and immediately writes a fresh snapshot owned by the restoring session.
- Documents discards its prior recovery session only after a replacement DOCX has parsed successfully; failed opens still preserve the current document and its recovery.
- Presentations performs the same bounded cleanup when a new presentation or successfully opened PPTX replaces the current one.
- Spreadsheet keeps its existing explicit discard-before-replacement flow, now made safe by session-scoped recovery deletion.
- Legacy snapshots without `sessionId` remain discoverable and restorable.
- Parsers, writers and visual layout are intentionally unchanged.

Full notes: [`docs/releases/RELEASE_NOTES_0.20.2.30.md`](docs/releases/RELEASE_NOTES_0.20.2.30.md)

Historical notes: [`docs/releases/`](docs/releases/)
