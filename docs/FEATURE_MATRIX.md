# Feature Matrix

| Capability | Documents | Spreadsheets | Presentations | Level |
|---|---:|---:|---:|---|
| Create blank OOXML file | DOCX | XLSX | PPTX | Core |
| Open basic OOXML file | DOCX | XLSX | PPTX | Core |
| Basic local editing | Yes | Yes | Yes | Core |
| Export a new copy | DOCX | XLSX | PPTX | Core |
| Package-preserving imported-file export | DOCX | XLSX | PPTX existing slide set | Best effort |
| Hidden worksheet state | — | Preserved and hidden from normal tabs | — | Best effort |
| Modern formula preview | — | XLOOKUP, FILTER, LET | — | Focused |
| Basic chart preview | — | Column/bar | Cached bar/column charts | Focused |
| Undo/redo | Yes | Yes | Yes | Core |
| Basic images | Raster | Raster worksheet drawings | Raster | Best effort |
| Simple tables | Yes | Grid and structured-table preview | Limited slide objects | Best effort |
| Presenter notes in editor | — | — | Yes | Best effort |
| Presenter notes in exported copy | — | — | Preserved for existing notes parts | Best effort |
| Present from first/current slide | — | — | Yes | Core |
| 4:3 and 16:9 | — | — | Yes | Core |
| Layout/master inheritance | — | — | Relationship-resolved preview | Best effort |
| Legacy binary `.xls` | — | BIFF8 import → XLSX copy | — | Focused |
| Macros/VBA | No | No | No | Unsupported |
| Pixel-identical Office rendering | No | No | No | Non-goal |

“Core” describes the intended workflow, not complete format coverage. Every file still requires validation.
