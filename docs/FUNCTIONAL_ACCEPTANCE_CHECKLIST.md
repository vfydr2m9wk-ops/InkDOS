# Functional acceptance checklist — InkDOS 1.0.0-beta.5

A visible function is not considered confirmed merely because the control exists. It needs behavioral automation or an explicit manual device check.

Visible controls: **221** · Automated: **87** · Scheduled: **134** · Manual: **0**

## Controls

### Home

- ⬜ `a[href="./index.html"]#1` — InkDOS home — **scheduled**
- ✅ `a[href="./apps/documents/index.html"]#1` — D Documents DOCX › — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `a[href="./apps/spreadsheets/index.html"]#1` — S Spreadsheets XLS · XLSX › — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `a[href="./apps/presentations/index.html"]#1` — P Presentations PPTX › — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `a[href="./apps/pdf/index.html"]#1` — PDF PDF Workspace PDF › — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `a[href="./apps/txt/index.html"]#1` — TXT Plain Text TXT › — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `a[href="./apps/epub/index.html"]#1` — EPUB EPUB Reader EPUB › — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ⬜ `a[href="https://github.com/vfydr2m9wk-ops/InkDOS"]#1` — Source — **scheduled**
- ⬜ `a[href="./docs/PROJECT_STATUS.md"]#1` — Status — **scheduled**
- ⬜ `a[href="./docs/KNOWN_LIMITATIONS.md"]#1` — Limitations — **scheduled**
- ⬜ `a[href="./CONTRIBUTING.md"]#1` — Contribute — **scheduled**

### Documents

- ⬜ `a[href="../../index.html"]#1` — Return to InkDOS home — **scheduled**
- ✅ `#newBtn` — New document — **automated** — tests/browser/revalidate_docx_three_eras.py; tests/browser/revalidate_local_recovery.py
- ⬜ `label[for="fileInput"]` — Open document — **scheduled**
- ⬜ `#undoBtn` — Undo — **scheduled**
- ⬜ `#redoBtn` — Redo — **scheduled**
- ⬜ `#sidebarBtn` — Toggle sidebar — **scheduled**
- ⬜ `#titleText` — Document name — **scheduled**
- ✅ `#saveBtn` — Save — **automated** — tests/browser/revalidate_docx_three_eras.py; tests/browser/revalidate_local_recovery.py
- ⬜ `#styleSelect` — Paragraph style — **scheduled**
- ⬜ `#fontSelect` — Font — **scheduled**
- ⬜ `#sizeSelect` — Font size — **scheduled**
- ⬜ `#lineSpacing` — Line spacing — **scheduled**
- ⬜ `[data-cmd="bold"]` — Bold — **scheduled**
- ⬜ `[data-cmd="italic"]` — I — **scheduled**
- ⬜ `[data-cmd="underline"]` — U — **scheduled**
- ⬜ `[data-cmd="justifyLeft"]` — ≡ — **scheduled**
- ⬜ `[data-cmd="justifyCenter"]` — ≣ — **scheduled**
- ⬜ `[data-cmd="justifyRight"]` — ≡ — **scheduled**
- ⬜ `[data-cmd="justifyFull"]` — ☰ — **scheduled**
- ⬜ `[data-cmd="insertUnorderedList"]` — • List — **scheduled**
- ⬜ `[data-cmd="insertOrderedList"]` — 1. List — **scheduled**
- ⬜ `#alphaList` — A. List — **scheduled**
- ⬜ `#tableBtn` — Table — **scheduled**
- ⬜ `#rowBtn` — Add table row — **scheduled**
- ⬜ `#colBtn` — Add table column — **scheduled**
- ⬜ `label[for="imageInput"]` — Image — **scheduled**
- ⬜ `[data-panel="pagesPanel"]` — Pages — **scheduled**
- ⬜ `[data-panel="outlinePanel"]` — Outline — **scheduled**
- ⬜ `[data-panel="searchPanel"]` — Search — **scheduled**
- ⬜ `#searchInput` — searchInput — **scheduled**
- ⬜ `#prevHit` — ↑ — **scheduled**
- ⬜ `#nextHit` — ↓ — **scheduled**
- ✅ `#newWelcomeBtn` — + New document — **automated** — tests/browser/revalidate_docx_three_eras.py; tests/browser/revalidate_local_recovery.py
- ⬜ `label[for="fileInput"]` — Open document — **scheduled**
- ⬜ `#zoomOut` — Zoom out — **scheduled**
- ⬜ `#zoomSlider` — Zoom level — **scheduled**
- ⬜ `#zoomIn` — Zoom in — **scheduled**
- ⬜ `#fitWidth` — Fit width — **scheduled**
- ⬜ `#zoomLabel` — Reset zoom — **scheduled**

### Spreadsheets

- ⬜ `a[href="../../index.html"]#1` — Return to InkDOS home — **scheduled**
- ⬜ `#newBtn` — New workbook — **scheduled**
- ⬜ `#openBtn` — Open workbook — **scheduled**
- ⬜ `#undoBtn` — Undo — **scheduled**
- ⬜ `#redoBtn` — Redo — **scheduled**
- ✅ `#docTitle` — Workbook name — **automated** — tests/test_functional_regressions.py; tests/browser/revalidate_functional_regressions.py
- ⬜ `#saveBtn` — Save XLSX copy — **scheduled**
- ⬜ `#fontFamily` — Font — **scheduled**
- ⬜ `#fontSize` — Font size — **scheduled**
- ⬜ `#boldBtn` — Bold — **scheduled**
- ⬜ `#italicBtn` — Italic — **scheduled**
- ⬜ `#underlineBtn` — Underline — **scheduled**
- ⬜ `#alignLeftBtn` — Align left — **scheduled**
- ⬜ `#alignCenterBtn` — Align center — **scheduled**
- ⬜ `#alignRightBtn` — Align right — **scheduled**
- ⬜ `#mergeBtn` — Merge or unmerge selected cells — **scheduled**
- ⬜ `#addRowBtn` — Insert row below — **scheduled**
- ⬜ `#addColBtn` — Insert column right — **scheduled**
- ⬜ `#deleteBtn` — Clear selected cells — **scheduled**
- ⬜ `#deleteRowBtn` — Delete selected rows — **scheduled**
- ⬜ `#deleteColBtn` — Delete selected columns — **scheduled**
- ⬜ `#operationSelect` — Operations — **scheduled**
- ⬜ `#gridMode` — Sheet — **scheduled**
- ⬜ `#formMode` — Page — **scheduled**
- ⬜ `#gridlinesBtn` — Show or hide gridlines — **scheduled**
- ⬜ `#nameBox` — Cell reference — **scheduled**
- ✅ `#formulaInput` — Formula bar — **automated** — tests/test_spreadsheet_formula_editor.py; tests/test_spreadsheet_formula_references.py; tests/browser/revalidate_workspace_consistency.py
- ⬜ `#newEmptyBtn` — + New document — **scheduled**
- ⬜ `#openEmptyBtn` — Open document — **scheduled**
- ⬜ `#zoomOut` — Zoom out — **scheduled**
- ⬜ `#zoomSlider` — Zoom — **scheduled**
- ⬜ `#zoomIn` — Zoom in — **scheduled**
- ⬜ `#fitWidth` — Fit width — **scheduled**
- ⬜ `#downloadBtn` — Save XLSX copy — **scheduled**
- ⬜ `#closeSaveBtn` — Cancel — **scheduled**

### Presentations

- ✅ `a[href="../../index.html"]#1` — Return to InkDOS home — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#newBtn` — + New document — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#openBtn` — Open document — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `a[href="../../index.html"]#2` — Return to InkDOS home — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#newSmall` — New Presentation — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#openSmall` — Open Presentation — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#undoBtn` — Undo — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#redoBtn` — Redo — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#docTitle` — Presentation name — **automated** — tests/test_functional_regressions.py; tests/browser/revalidate_functional_regressions.py
- ✅ `#presentFromStartTop` — Present from first slide — **automated** — tests/browser/revalidate_presentations_slideshow.py
- ✅ `#presentFromCurrentTop` — Present from current slide — **automated** — tests/browser/revalidate_presentations_slideshow.py
- ✅ `#saveBtn` — Save PPTX copy — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `[data-tab="home"]` — Home — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `[data-tab="insert"]` — Insert — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `[data-tab="arrange"]` — Arrange — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `[data-tab="view"]` — View — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `[data-tab="present"]` — Present — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#addSlideBtn` — New slide ▾ — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#dupSlideBtn` — Duplicate — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#delSlideBtn` — Delete — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#fontFamily` — Arial Aptos Calibri Georgia Helvetica Times New Roman — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#fontSize` — 12 16 20 24 32 44 60 — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#boldBtn` — B — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#italicBtn` — I — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#alignLeft` — ⇤ — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#alignCenter` — ≡ — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#alignRight` — ⇥ — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#insertTextBtn` — Text — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#insertImageBtn` — Image — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#shapeType` — Shape type — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#insertShapeBtn` — Insert shape — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#frontBtn` — Bring front — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#backBtn` — Send back — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#deleteObjBtn` — Delete object — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#togglePresentationsBtn` — Hide thumbnails — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#toggleInspectorBtn` — Show format panel — **automated** — tests/browser/revalidate_presentations_controls.py; tests/test_presentations_responsive_controls.py
- ✅ `#toggleNotesBtn` — Show presenter notes — **automated** — tests/browser/revalidate_presentations_controls.py; tests/test_presentations_responsive_controls.py
- ✅ `#presentViewBtn` — Present current — **automated** — tests/browser/revalidate_presentations_slideshow.py
- ✅ `#zoomOutBtn` — − — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#zoomRange` — + Fit — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#zoomInBtn` — + — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#fitBtn` — Fit — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#transitionType` — None Fade Slide Zoom — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#presentFromStartBtn` — From first slide — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#presentFromCurrentBtn` — From current slide — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#propX` — propX — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#propY` — propY — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#propW` — propW — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#propH` — propH — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#propOpacity` — propOpacity — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#propFill` — propFill — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#propRotation` — propRotation — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#cropZoom` — cropZoom — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#cropX` — cropX — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#cropY` — cropY — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#resetCropBtn` — Reset crop — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#presenterNotes` — presenterNotes — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#bottomZoomOutBtn` — Zoom out — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#bottomZoomRange` — Zoom level — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#bottomZoomInBtn` — Zoom in — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#bottomFitBtn` — Fit slide — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `#exitPresentBtn` — Exit presentation — **automated** — tests/browser/revalidate_presentations_slideshow.py
- ✅ `#closeTemplateBtn` — Close — **automated** — tests/browser/revalidate_presentations_controls.py

### PDF

- ⬜ `a[href="../../index.html"]#1` — Return to InkDOS home — **scheduled**
- ⬜ `#openBtn` — Open document — **scheduled**
- ⬜ `a[href="../../index.html"]#2` — InkDOS home — **scheduled**
- ⬜ `#openSmall` — Open PDF — **scheduled**
- ⬜ `#sidebarToggle` — Toggle navigation panel — **scheduled**
- ⬜ `#saveModifiedPdfBtn` — Save annotated PDF — **scheduled**
- ⬜ `#fullscreenBtn` — Full screen — **scheduled**
- ⬜ `#systemOpenBtn` — Open in system viewer — **scheduled**
- ⬜ `#verticalScroll` — Continuous vertical scrolling — **scheduled**
- ⬜ `#horizontalScroll` — Horizontal document scrolling — **scheduled**
- ⬜ `[data-tool="select"]` — Select PDF text or fill AcroForm fields — **scheduled**
- ⬜ `[data-tool="highlight"]` — Highlight selected text — **scheduled**
- ⬜ `[data-tool="underline"]` — Underline selected text — **scheduled**
- ⬜ `[data-tool="marker"]` — Free marker area — **scheduled**
- ⬜ `[data-tool="comment"]` — Comment on selected text — **scheduled**
- ⬜ `[data-tool="text"]` — Insert free text — **scheduled**
- ⬜ `#undoReview` — Undo last review action — **scheduled**
- ⬜ `#bookmarkBtn` — Add or remove bookmark — **scheduled**
- ⬜ `[data-tab="pages"]` — Pages — **scheduled**
- ⬜ `[data-tab="outline"]` — Index — **scheduled**
- ⬜ `[data-tab="bookmarks"]` — Bookmarks — **scheduled**
- ⬜ `[data-tab="comments"]` — Comments — **scheduled**
- ⬜ `#prevPage` — Previous page — **scheduled**
- ⬜ `#pageNumber` — Page number — **scheduled**
- ⬜ `#nextPage` — Next page — **scheduled**
- ⬜ `#zoomOut` — Zoom out — **scheduled**
- ⬜ `#pdfZoomSlider` — Zoom level — **scheduled**
- ⬜ `#zoomIn` — Zoom in — **scheduled**
- ⬜ `#pdfFitWidth` — Fit width — **scheduled**
- ⬜ `#immersiveExit` — Exit full screen — **scheduled**
- ⬜ `#textDialogValue` — textDialogValue — **scheduled**
- ⬜ `#dialogCancel` — Cancel — **scheduled**
- ⬜ `button:insert#1` — Insert — **scheduled**

### TXT

- ⬜ `a[href="../../index.html"]#1` — InkDOS home — **scheduled**
- ✅ `#newBtn` — New text file — **automated** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- ✅ `#openBtn` — Open text file — **automated** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- ⬜ `#undoBtn` — Undo — **scheduled**
- ⬜ `#redoBtn` — Redo — **scheduled**
- ⬜ `#docTitle` — Text file name — **scheduled**
- ✅ `#saveBtn` — Save text file — **automated** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- ✅ `#wrapBtn` — Wrap — **automated** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- ⬜ `#fontSize` — Text size — **scheduled**
- ✅ `#findBtn` — Find — **automated** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- ⬜ `#findInput` — Find text — **scheduled**
- ✅ `#findPrevious` — Previous result — **automated** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- ✅ `#findNext` — Next result — **automated** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- ⬜ `#findClose` — Close find — **scheduled**
- ⬜ `#newStartBtn` — + New document — **scheduled**
- ⬜ `#openStartBtn` — Open document — **scheduled**
- ⬜ `#editor` — Plain text editor — **scheduled**
- ⬜ `#txtZoomOut` — Zoom out — **scheduled**
- ⬜ `#txtZoomSlider` — Zoom level — **scheduled**
- ⬜ `#txtZoomIn` — Zoom in — **scheduled**
- ⬜ `#txtFit` — Fit editor — **scheduled**

### EPUB

- ⬜ `a[href="../../index.html"]#1` — InkDOS home — **scheduled**
- ✅ `#openBtn` — Open EPUB — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `#tocBtn` — Table of contents — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ⬜ `#docTitle` — EPUB file name — **scheduled**
- ⬜ `#saveBtn` — Save renamed EPUB copy — **scheduled**
- ✅ `#fontDecrease` — Decrease text size — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `#fontIncrease` — Increase text size — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ⬜ `[data-theme="paper"]` — Paper theme — **scheduled**
- ⬜ `[data-theme="sepia"]` — Sepia theme — **scheduled**
- ⬜ `[data-theme="sage"]` — Sage theme — **scheduled**
- ⬜ `[data-theme="night"]` — Night theme — **scheduled**
- ⬜ `#tocClose` — Close contents — **scheduled**
- ⬜ `#openStartBtn` — Open document — **scheduled**
- ✅ `#previousPage` — Previous page — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `#nextPage` — Next page — **automated** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- ⬜ `#epubZoomOut` — Zoom out — **scheduled**
- ⬜ `#epubZoomSlider` — Zoom level — **scheduled**
- ⬜ `#epubZoomIn` — Zoom in — **scheduled**
- ⬜ `#epubFit` — Fit page — **scheduled**

## Capabilities

- ✅ `global.version-integrity` — Version/cache/release metadata are synchronized — **automated** — tests/test_workspace_consistency.py; tests/browser/revalidate_workspace_consistency.py; scripts/verify_checksums.py
- ✅ `global.offline-launch` — Application shell launches from service-worker cache with versioned URLs — **automated** — tests/browser/revalidate_launch_and_offline_modes.py
- ✅ `global.cross-workspace-isolation` — Workspace state and file handoff do not leak across modules — **automated** — tests/browser/revalidate_cross_workspace_isolation.py
- ✅ `global.interactive-dom-contracts` — Workspace DOM ids and direct app control references resolve without duplicates or orphan targets — **automated** — tests/test_interactive_dom_contracts.py
- ✅ `documents.recovery` — IndexedDB recovery: Restore / Open normally / Discard — **automated** — tests/test_local_recovery.py; tests/browser/revalidate_local_recovery.py
- ✅ `spreadsheets.recovery` — IndexedDB recovery: Restore / Open normally / Discard — **automated** — tests/test_local_recovery.py; tests/browser/revalidate_local_recovery.py
- ✅ `presentations.recovery` — IndexedDB recovery: Restore / Open normally / Discard — **automated** — tests/test_local_recovery.py; tests/browser/revalidate_local_recovery.py
- ✅ `presentations.format-panel-responsive` — Format panel has one open/closed state across desktop and compact/iPad-width layouts and edits selected objects — **automated** — tests/browser/revalidate_presentations_controls.py
- ✅ `spreadsheets.multi-cell-selection` — Multi-cell selection remains separate from formula reference mode — **automated** — tests/test_spreadsheet_formula_references.py; tests/browser/revalidate_workspace_consistency.py
- ✅ `pdf.unified-save` — Single PDF Save action preserves supported annotations/forms — **automated** — tests/test_pdf_unified_save.py
- 🟨 `manual.safari-ipad` — Native Safari/iPadOS touch, file picker, download and installed-PWA behavior — **manual** — manual device matrix
- 🟨 `manual.edge-windows` — Native Edge/Windows file picker, download and clipboard behavior — **manual** — manual device matrix
- ✅ `home.compact-release-copy` — home.compact-release-copy — **automated** — tests/test_functional_regressions.py; tests/browser/revalidate_functional_regressions.py
- ✅ `spreadsheets.editable-title` — spreadsheets.editable-title — **automated** — tests/test_functional_regressions.py; tests/browser/revalidate_functional_regressions.py
- ✅ `presentations.editable-title` — presentations.editable-title — **automated** — tests/test_functional_regressions.py; tests/browser/revalidate_functional_regressions.py
- ✅ `pdf.obsolete-forms-note-removed` — pdf.obsolete-forms-note-removed — **automated** — tests/test_functional_regressions.py; tests/browser/revalidate_functional_regressions.py
- ✅ `txt-epub.primary-titlebar-44px` — txt-epub.primary-titlebar-44px — **automated** — tests/test_functional_regressions.py; tests/browser/revalidate_functional_regressions.py
