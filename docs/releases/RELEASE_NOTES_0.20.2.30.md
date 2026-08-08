# InkDesk v0.20.2.30 — Recovery Session Isolation Hardening

## Why this release exists

Recovery identity previously used only the Office file key. Two tabs opening the same file therefore shared the same recovery deletion scope: a discard/reset in one tab could remove snapshots created by the other. Documents and Presentations also avoided some cleanup, which could leave recovery from work the user had explicitly replaced.

## Changes

- Adds a unique recovery `sessionId` per local-recovery manager.
- Stores `sessionId` on new snapshot schema version 2 records.
- Scopes snapshot reset, clean and discard operations to `documentKey + sessionId`.
- Applies the rolling three-snapshot limit per document session.
- Keeps legacy sessionless snapshots readable and gives them their own legacy recovery group.
- Re-homes a restored recovery by deleting the recovered session's old snapshot set and flushing a fresh snapshot in the restoring session.
- Documents now discards only its own previous recovery session after the replacement DOCX is successfully parsed and committed; New document also explicitly discards the previous session.
- Presentations applies the same transition through its recovery controller for successful PPTX replacement and New presentation.
- Spreadsheet New now awaits the recovery document transition, closing a small asynchronous lifecycle gap.
- Shared source-package retention remains document-scoped so OOXML preservation data can still be reused/re-hydrated across tabs.

## Deliberately unchanged

No parser, writer, formula engine, PDF behavior, TXT/EPUB behavior or visual UI is changed. This patch is limited to recovery ownership and replacement lifecycle.
