# Compatibility and Validation Matrix

InkDesk provides focused, partial compatibility. “Passed” below means the listed scenario was actually executed; it does not imply complete format or platform support.

## Format scope

| Format | Status | Important limits |
|---|---|---|
| DOCX | Partial | Common paragraphs, headings, lists, tables, images, headers/footers, page breaks, and hyperlinks-as-inert-content; advanced fields, equations, comments, and complex drawings are incomplete |
| XLSX | Partial | Common sheets, cells, cached formulas, styles, merges, widths, images, dates, percentages, and relationships; formula and chart fidelity are limited |
| XLS (BIFF8) | Import only | Local import; export creates XLSX; older BIFF, VBA, OLE, and some records are unsupported |
| PPTX | Partial | Common slides, text, images, shapes, layouts/masters, notes preservation, themes, and relationships; advanced animation, SmartArt, media, and exact layout are incomplete |
| DOC / PPT binary | Unsupported | Controlled rejection; convert to DOCX/PPTX first |
| PDF | Out of scope | Use a dedicated PDF tool |

## Browser/platform evidence for 0.19.2-beta

| Environment | Open/edit/export/reopen | Offline/PWA | Status | Evidence/notes |
|---|---|---|---|---|
| Linux system Chromium via Playwright | Executed | Restricted-API and static-asset scenarios executed | Passed in local review | Automated synthetic/fixture scenarios; not native iPadOS |
| Playwright Firefox | Configured in CI | Configured in CI | Not tested locally | Requires CI or a local Playwright Firefox installation |
| Playwright WebKit | Configured in CI | Configured in CI | Not tested locally | Playwright WebKit is not native Safari or physical iPadOS |
| Desktop Safari | Not executed | Not executed | Not tested | Manual device validation required |
| Native Firefox desktop | Not executed | Not executed | Not tested | Playwright Firefox results must not be relabeled as native packaging validation |
| iPadOS Safari | Not executed | Not executed | Not tested | Download UI, memory pressure, touch, keyboard, background/return, and PWA require a physical device |
| Installed PWA | Not executed locally | Not executed locally | Not tested | Service-worker structure is statically checked; actual browser-controlled offline reload remains manual |
| Direct `file://` | Environment-dependent | Service worker unavailable | Not tested locally | Host/browser policies vary |
| Embedded/local-file hosts | Not executed | Host-specific | Not tested | No support claim |

## Unified opening and navigation

The main page detects `.docx`, `.xls`, `.xlsx`, and `.pptx` and selects the corresponding workspace. Hosted HTTP(S)/PWA use a one-time IndexedDB handoff. Direct `file://` uses an embedded same-package workspace and a token-scoped file bridge because local-file storage/origin behavior differs between browsers. Chromium script-level routing and bridge transfer were executed; physical iPadOS/Safari direct-file behavior remains manual validation.

All three workspaces expose a relative `../../index.html` home link with `target="_top"`, allowing the same control to leave a normal page or the local-file embedded workspace. On narrow screens, secondary history/zoom/presentation controls may be hidden from the title bar to protect the primary navigation, filename, and export action.

## Export semantics

“Download requested” means only that InkDesk invoked the browser mechanism. The state remains unverified and `beforeunload` protection remains active. Reopening an exported copy can mark it verified only when the SHA-256 fingerprint and byte length match the generated copy.

## Formula scope

The deterministic evaluator supports numeric literals, cell-reference substitution, parentheses, unary `+`/`-`, `+`, `-`, `*`, `/`, `%`, and `^`, plus the explicitly implemented focused functions in the spreadsheet workspace (including `SUM`, `AVERAGE`, `MIN`, `MAX`, `COUNT`, `ROUND`, `IF`, and limited `XLOOKUP`, `FILTER`, and `LET`). Unsupported formulas are preserved with cached values where available and are marked as not recalculated.
