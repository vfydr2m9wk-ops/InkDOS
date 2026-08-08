# InkDesk v0.20.2.31 — Recovery Prompt Startup Isolation Hardening

This maintenance release prevents a stale asynchronous recovery scan from appearing after the user has already started a different New/Open document action.

## Current release

- Startup recovery inspection is guarded by both a prompt epoch and the active document generation/key.
- A recovery prompt started for the empty startup state is abandoned if a document transition begins before IndexedDB inspection finishes.
- Documents and Spreadsheets explicitly cancel a pending recovery prompt before slow file parsing or a New-document transition.
- Presentations cancels a pending prompt as soon as a PPTX file is selected, before the potentially slower PPTX parse begins, and also cancels defensively inside its recovery transition controller.
- Cancelling/defering a stale prompt does **not** delete the older snapshot; it remains available on a later clean launch.
- Session isolation, source-package continuity and unverified-download protection from v0.20.2.30 and earlier remain unchanged.
- Parsers, writers, formula semantics and visual layout are intentionally unchanged.

Full notes: [`docs/releases/RELEASE_NOTES_0.20.2.31.md`](docs/releases/RELEASE_NOTES_0.20.2.31.md)

Historical notes: [`docs/releases/`](docs/releases/)
