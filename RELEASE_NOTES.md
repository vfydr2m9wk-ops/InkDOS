# InkDesk v0.20.2.27 — Recovery Source Rehydration and Metadata Continuity Hardening

This release hardens recovery-source continuity across browser tabs and makes release metadata self-checking.

## Current release

- Recovery snapshots can rehydrate a missing imported source package from the still-active editing session before the snapshot is committed.
- Fresh clean-session sources are no longer deleted immediately as apparent orphans by another tab.
- Recovery cleanup defers or rewrites safely when edits race with an in-flight cleanup.
- Public release entry points are checked against `VERSION.json` so README/release-note drift fails validation.

Full notes: [`docs/releases/RELEASE_NOTES_0.20.2.27.md`](docs/releases/RELEASE_NOTES_0.20.2.27.md)

Historical notes: [`docs/releases/`](docs/releases/)
