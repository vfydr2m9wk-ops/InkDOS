# InkDesk v0.20.2.31 — Recovery Prompt Startup Isolation Hardening

## Why this release exists

The final structural audit found a startup race in the shared local-recovery prompt. `promptLatest()` queries IndexedDB asynchronously. Before this release, a user could begin New/Open while that query was still in flight; the older recovery prompt could then appear after the active document had already changed. Restoring that stale prompt could replace the newly started work without a fresh discard decision.

This is most plausible on slower storage/browser paths such as Safari/iPadOS, where IndexedDB startup can take noticeably longer than on desktop Chromium.

## Changes

- Add a prompt epoch to the shared recovery manager.
- Bind each recovery inspection to the document generation and document key that existed when inspection started.
- Suppress a prompt if either the prompt token or active-document identity changes while IndexedDB work is pending.
- Expose `cancelPrompt()` for an explicit user-initiated document transition.
- Documents cancels before DOCX parsing and before New-document cleanup.
- Spreadsheets cancels before XLS/XLSX parsing and before New-workbook cleanup.
- Presentations cancels as soon as a selected PPTX begins opening and defensively in New/Open recovery transitions.
- Preserve the older recovery snapshot when a prompt is deferred; only the stale UI prompt is cancelled.
- Add a deterministic browser regression that starts `promptLatest()`, changes documents before it resolves, and proves the stale prompt is not rendered while the older snapshot remains available.

## Deliberately unchanged

No Office parser/writer, Spreadsheet formula/history behavior, PDF/TXT/EPUB behavior or visual layout is changed. `shared/local-recovery.js` remains at its existing 276-line architecture ratchet.
