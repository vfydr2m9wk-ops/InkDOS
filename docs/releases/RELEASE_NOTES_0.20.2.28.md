# InkDesk v0.20.2.28 — Documents Replacement Transaction Safety Hardening

## Risk found

The Documents workspace had its own dirty state and protected New-document replacement, but `openFile()` did not consult that state. Because the shared document-session adapter does not own Documents content edits, selecting another DOCX could replace an edited document without an application-level confirmation.

## Hardening

- `openFile()` now checks the Documents dirty state before any replacement work begins.
- Rejecting the prompt clears the pending file input and preserves the current document.
- Accepting the prompt only authorizes an attempted replacement; the existing transactional rollback still restores the complete previous state if parsing fails.
- The existing transactional Chromium regression now modifies the current DOCX, proves cancellation preserves it, then accepts a corrupt replacement and proves the unsaved document still survives the failed open.

## Scope

This is a targeted data-safety fix. No visual redesign, editor command, DOCX parser/writer capability or recovery schema is changed.
