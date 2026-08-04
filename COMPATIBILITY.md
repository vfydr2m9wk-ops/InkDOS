# Compatibility

InkDesk provides partial, focused compatibility rather than complete Microsoft Office fidelity.

| Format | Status | Notes |
|---|---|---|
| DOCX | Partially supported | Common text, formatting, images, tables, lists, sections, headers, and footers |
| XLSX | Partially supported | Common cells, styles, worksheets, formulas, images, and package-preserving export |
| XLS (BIFF8) | Import only | Imported locally and saved as a new XLSX copy |
| PPTX | Partially supported | Common slides, text, images, layouts, masters, notes resolution, chart previews, and presentation mode |
| DOC / PPT binary | Unsupported | Rejected with a controlled message |
| PDF | Out of scope | Use a dedicated PDF viewer/editor |

## Browser and host status

| Environment | Review status |
|---|---|
| System Chromium through Playwright | Automated workflows passed |
| Chromium touch emulation with unavailable storage, clipboard, fullscreen, and service-worker APIs | Automated fallback checks passed |
| Static HTTP asset delivery | Verified with a local server |
| Direct `file://` navigation in the review Chromium | Not performed; blocked by an administrative browser policy |
| Hosted PWA installation and browser-controlled offline reload | Not performed; browser navigation was blocked by the same policy |
| Native Firefox | Not performed; browser unavailable |
| Native Safari/WebKit | Not performed; browser unavailable |
| Native iPadOS / embedded WebKit host | Not performed; device unavailable |
| Edge | Historical manual use only; not part of this review evidence |

Local `file://` behavior depends on host security policies. Static HTTP(S) hosting is the most predictable deployment mode. A passing Chromium test does not establish Safari, Firefox, or iPadOS compatibility.
