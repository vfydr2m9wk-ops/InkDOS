# Compatibility

InkDesk 1.0 beta provides focused compatibility rather than complete Microsoft Office fidelity.

| Format | Status | Notes |
|---|---|---|
| DOCX | Partially supported | Common text, formatting, images, tables, lists, sections, headers/footers and package-preserving copy export |
| XLSX | Partially supported | Common cells, styles, worksheets, supported formulas, images and package-preserving export |
| XLS (BIFF8) | Import only | Imported locally and saved as a new XLSX copy |
| PPTX | Partially supported | Common slides, text, images, backgrounds/layouts, notes resolution and slideshow |
| PDF | Focused support | Local viewing, navigation, review/annotations and save within the documented subset |
| TXT | Supported | Plain-text local editing |
| EPUB | Focused support | Reflowable local EPUB reading; DRM/fixed-layout excluded |
| DOC / PPT binary | Unsupported | Use a supported modern format |

## Browser and host status

| Environment | 1.0 beta evidence |
|---|---|
| Chromium through Playwright | Automated release regressions |
| Chromium touch/coarse-pointer paths | Automated targeted coverage |
| Static HTTP asset delivery | Validated by repository/browser harnesses |
| Direct `file://` | Supported where host policy permits; less predictable than HTTP(S) |
| Firefox | Optional matrix / manual evidence when engine is available |
| Safari/WebKit | Requires native/target-device validation |
| iPadOS / embedded WebKit host | Requires target-device validation |
| Installed PWA/offline reload | Requires target-browser validation |

A passing Chromium suite does not establish Safari, Firefox or iPadOS compatibility.
