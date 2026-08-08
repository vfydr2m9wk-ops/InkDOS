# InkDesk v0.20.2.28 — Documents Replacement Transaction Safety Hardening

This release closes a direct unsaved-document replacement path in the Documents workspace.

## Current release

- Opening another DOCX while the active document is dirty now requires explicit discard confirmation.
- Cancelling that confirmation leaves the edited DOCX and its dirty state untouched.
- If the user confirms replacement but the selected DOCX fails to parse, the previous unsaved document is restored transactionally.
- The regression suite now exercises both cancellation and confirmed-but-failed replacement against a deliberately modified DOCX.
- No visual, formatting, ruler, DOCX writer or file-format behavior is intentionally changed.

Full notes: [`docs/releases/RELEASE_NOTES_0.20.2.28.md`](docs/releases/RELEASE_NOTES_0.20.2.28.md)

Historical notes: [`docs/releases/`](docs/releases/)
