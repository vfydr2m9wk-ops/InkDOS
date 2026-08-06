# InkDesk v0.20.0 — Consolidated Modular Preview

Released: 2026-08-06

## What changed

- Consolidated the 0.19.4 development line into one complete package.
- Introduced a cleaner six-workspace home page and public Semantic Versioning.
- Included Documents, Spreadsheets, Presentations, PDF, Plain Text and EPUB.
- Preserved the rounded shared visual system and native system typography.
- Preserved editable filenames and unsaved-change protection where applicable.
- Reset future patch development to the 0.20.x line.

## Important limitations

InkDesk remains experimental. Compatibility is intentionally focused, exported
copies must be reopened and verified for important work, and saving usually
creates a new downloaded file. EPUB is read-only apart from saving the original
book under a renamed filename.


### Pinned PDF.js publication step

The source publication workflow installs the exact `pdfjs-dist@3.11.174`
classic build before strict validation. InkDesk disables PDF.js eval support
when opening a document. The committed release remains self-contained and
offline after publication.
