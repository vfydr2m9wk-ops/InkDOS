# Compatibility

InkDesk provides partial, focused compatibility rather than complete Microsoft Office fidelity.

| Format | Status | Notes |
|---|---|---|
| DOCX | Partial | Common content plus section size, A4 margins, headers, footers and common table geometry |
| XLSX | Partial | Common cells, styles, worksheets, formulas, drawings and page-oriented preview |
| XLS (BIFF8) | Import only | Local import; save creates an XLSX copy; sheet zero-display options are respected |
| PPTX | Partial | Common slides, direct/layout/master backgrounds, images, transforms, tables and presentation mode |
| PDF | Preview only | Local native-browser rendering; no editing or conversion |
| DOC / PPT binary | Unsupported | Controlled rejection |

## Browser and host status

The current PDF and spreadsheet changes were exercised in system Edge/Chromium automation. The selectable-text/outline PDF rendered with no page errors, and the synthetic 4,000-page PDF jumped to page 3,500 while retaining five full page canvases and 25 thumbnail canvases. Spreadsheet formula suggestions and a 3×3 pointer-drag selection were also exercised. Native Safari, Firefox, physical iPadOS, installed PWA behavior and embedded hosts were not executed and must not be inferred from Chromium results.
