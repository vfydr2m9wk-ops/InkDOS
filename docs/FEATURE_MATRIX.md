# Feature Matrix

| Capability | Documents | Spreadsheets | Presentations | PDF Workspace | Level |
|---|---:|---:|---:|---:|---|
| Open local file | DOCX | XLS/XLSX | PPTX | PDF from hub or workspace | Core |
| Create blank file | DOCX | XLSX | PPTX | — | Core |
| Basic local editing | Yes | Yes | Yes | Review overlay only | Core / partial |
| Export/download copy | DOCX | XLSX | PPTX | Original PDF + review JSON | Core |
| A4/page geometry | Section/page size, margins | Paper/orientation/margins/fit | Slide size | Native engine | Best effort |
| Headers and footers | Yes | Imported print metadata only | Slide master/footer objects partial | Native engine | Best effort |
| Tables | Widths, merges, fills, borders | Grid, merges and borders | Grid widths, row heights, merges, fills and borders | Native engine | Best effort |
| Images | Raster | BIFF8/OOXML drawings | Raster and direct background images | Native engine | Best effort |
| Undo/redo | Yes | Yes | Yes | Review Undo | Core / partial |
| Page thumbnails | Page thumbnails | Print preview | Slide thumbnails | Native thumbnail attempts / numbered fallback | Partial |
| Index/outline | Heading outline | Sheet tabs | Slide list | PDF outline inspection | Partial |
| Vertical/horizontal navigation | Page flow | Grid/page view | Slide list | Host mode + native view hint | Partial |
| Fullscreen | Browser/host dependent | Browser/host dependent | Presentation mode | Fullscreen API + immersive fallback | Core |
| Forms | Content controls partial | Cell inputs | — | Native AcroForm interaction | Browser-dependent |
| Highlight/underline/marker | Text formatting | Cell formatting | Text formatting | Region-based local review layer | Partial |
| Comments/inserted text | Partial | Notes partial | Speaker notes partial | Local review layer | Partial |
| Personal bookmarks | Outline | Sheet navigation | Slide navigation | Local PDF fingerprint bookmarks | Core |
| Present from first/current | — | — | Yes | — | Core |
| Legacy binary `.xls` | — | BIFF8 import → XLSX copy | — | — | Focused |
| Macros/VBA/active content | No | No | No | No execution | Unsupported |
| Pixel-identical Office/Edge rendering | No | No | No | No | Non-goal |

“Core” describes the intended workflow, not complete format coverage. Every important file still requires validation.
