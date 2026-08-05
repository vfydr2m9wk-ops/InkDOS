# Manual Device Checklist — 0.19.3-beta.7

Record date, exact browser build, OS/device, host mode, fixture and result. Preserve screenshots/logs without private documents.

| Environment | DOCX | XLS/XLSX | PPTX | PDF | Offline/PWA | Current result |
|---|---|---|---|---|---|---|
| Desktop Safari | — | — | — | — | — | Not tested |
| Native desktop Firefox | — | — | — | — | — | Not tested |
| iPadOS Safari | — | — | — | — | — | Not tested |
| Installed PWA | — | — | — | — | — | Not tested |
| Direct `file://` where allowed | — | — | — | — | N/A | Not tested |
| Embedded/local-file host | — | — | — | — | Host-specific | Not tested |

For each environment test all four workspaces. For editable formats, verify open, edit, export request and reopen. Also verify service-worker updates where applicable.

For PDF 0.19.3-beta.7, record these checks separately:

1. open a normal PDF and confirm previous/next, page entry, scrolling and the Pages panel all select the same rendered page;
2. open a book near 600 pages, jump to pages 2, 300 and the last page, and confirm the viewer does not remain on page 1;
3. open the synthetic 4,000-page fixture, jump directly to page 3,500, and confirm the Pages panel remains a small moving window;
4. verify that one PDF object and one nested embed exist, with no PDF iframe;
5. exercise Fit page, Fit width, 50%, 100%, 200%, 300% and 400%;
6. enter and exit full screen using the same button, Escape and the visible Exit full screen control;
7. repeat open/close with several PDFs and watch for browser or host termination;
8. verify external/system-viewer fallback and unchanged original-file download.

Do not use private documents for screenshots or logs.
