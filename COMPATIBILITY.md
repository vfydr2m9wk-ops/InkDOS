# Compatibility and Validation Matrix

InkDesk provides focused, partial compatibility. “Passed” means the listed scenario was executed; it does not imply complete Microsoft Office, Microsoft Edge or browser support.

## Format scope

| Format | Status | Important limits |
|---|---|---|
| DOCX | Partial | A4/section dimensions, margins, paragraphs, lists, images, headers, footers and common tables are rendered; BOM-prefixed XML is normalized; fields, equations, comments, tracked changes and complex DrawingML remain partial |
| XLSX | Partial | Common cells, styles, formulas with cached values, merges, widths/heights, images and page setup are supported; external data, pivots, macros and advanced charts are not |
| XLS (BIFF8) | Import only | Local import with styles, merges, images, print geometry and sheet-level zero-display behavior; saving creates an XLSX copy |
| PPTX | Partial | Common text, images, shapes, slide/layout/master backgrounds, transforms and tables are rendered; SmartArt, media, advanced animation and exact text layout remain partial |
| PDF | Native preview + local review layer | Bounded file inspection, one viewer instance, windowed page navigation and 50%–400% zoom are provided; page rendering/forms still depend on the browser engine, and review/form values are not written into PDF bytes |
| DOC / PPT binary | Unsupported | Convert to DOCX/PPTX first |

## Validation evidence for 0.19.3-beta.7

| Environment | Status | Evidence |
|---|---|---|
| Edge/Chromium, direct `file://` and local hub iframe | Passed for current automated scope | The extracted release ZIP registered the real PDF file chooser, opened the selectable-text/AcroForm fixture directly and through the hub without a timeout, and opened the synthetic 4,000-page PDF at page 3,500 with five full canvases. Presentation progress and direct `=` formula suggestions were exercised from the extracted ZIP. |
| Supplied real-world DOCX, XLS and PPTX samples | Passed in local Chromium review | DOCX: A4 page/header/footer; XLS: page-oriented form with borders/images and hidden zero values; PPTX: 43 slides and direct background image |
| Firefox / Safari / WebKit / physical iPadOS | Not tested | Manual validation is still required, especially worker loading, long-PDF memory behavior and PDF form-value persistence |
| Installed PWA/offline reload | Not tested end-to-end | App-shell inventory is statically validated; device/browser behavior remains manual |
| Direct `file://` / embedded hosts | Environment-dependent | Host module/worker policies vary; hosted HTTPS/PWA delivery is preferred when a shell blocks local workers |

## Unified opening and navigation

The hub selector accepts `.docx`, `.xls`, `.xlsx`, `.pptx` and `.pdf` and opens the matching workspace. All four workspaces expose a home control. Hosted HTTP(S)/PWA mode uses the normal workspace route; direct local-file behavior remains browser-dependent.

## Export semantics

“Download requested” means InkDesk invoked the browser download mechanism. DOCX/XLSX/PPTX copies should be reopened and verified before the originals are discarded. The PDF Workspace downloads the unchanged original PDF and can separately export its anonymized review sidecar.
