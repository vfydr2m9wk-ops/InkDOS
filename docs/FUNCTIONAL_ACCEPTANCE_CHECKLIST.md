# Functional acceptance checklist — InkDesk 0.20.2

This is the persistent inventory for user-facing InkDesk functions. A control is **not** considered confirmed simply because it renders or has a click handler. Confirmation requires behavioral automation or an explicit manual device check.

Legend: **[x] automated** = behavior has regression evidence; **[ ] scheduled** = visible function is inventoried but still needs dedicated behavior coverage; **[M] manual** = device/browser behavior that must be checked manually.

## Release policy

- Every new visible control must be added to the machine-readable matrix before release.
- Changed controls should receive a targeted behavioral test in the same release whenever practical.
- Platform-specific items are recorded as manual/not-performed; Chromium success is never used as proof of Safari/iPadOS, Firefox or Edge behavior.
- A failed behavioral gate rolls the update transaction back.

## Capability-level gates

- [x] **global — Version/cache/release metadata are synchronized** — automated — `tests/test_v0201_consistency.py, tests/browser/revalidate_v0201_consistency.py, scripts/verify_checksums.py`
- [x] **global — Application shell launches from service-worker cache with versioned URLs** — automated — `tests/browser/revalidate_launch_and_offline_modes.py`
- [x] **global — Workspace state and file handoff do not leak across modules** — automated — `tests/browser/revalidate_cross_workspace_isolation.py`
- [x] **global — Workspace DOM ids and direct app control references resolve without duplicates or orphan targets** — automated — `tests/test_interactive_dom_contracts.py`
- [x] **documents — IndexedDB recovery: Restore / Open normally / Discard** — automated — `tests/test_local_recovery.py, tests/browser/revalidate_v0202_local_recovery.py`
- [x] **spreadsheets — IndexedDB recovery: Restore / Open normally / Discard** — automated — `tests/test_local_recovery.py, tests/browser/revalidate_v0202_local_recovery.py`
- [x] **presentations — IndexedDB recovery: Restore / Open normally / Discard** — automated — `tests/test_local_recovery.py, tests/browser/revalidate_v0202_local_recovery.py`
- [x] **presentations — Format panel opens/closes and edits selected objects on desktop and compact/iPad-width layouts** — automated — `tests/browser/revalidate_presentations_controls.py`
- [x] **spreadsheets — Multi-cell selection remains separate from formula reference mode** — automated — `tests/test_spreadsheet_formula_references.py, tests/browser/revalidate_v0201_consistency.py`
- [x] **pdf — Single PDF Save action preserves supported annotations/forms** — automated — `tests/test_pdf_unified_save.py`
- [M] **global — Native Safari/iPadOS touch, file picker, download and installed-PWA behavior** — manual — `manual device matrix`
- [M] **global — Native Edge/Windows file picker, download and clipboard behavior** — manual — `manual device matrix`

## Visible-control inventory

Current inventory: **210 controls**. Automated behavioral evidence currently covers **86**; **124** are explicitly scheduled for progressive coverage rather than being assumed to work.

### Home

- [ ] `home.inkdesk-home` — **InkDesk home** — dedicated behavioral confirmation pending
- [x] `home.d-documents-docx` — **D Documents DOCX ›** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `home.s-spreadsheets-xls-xlsx` — **S Spreadsheets XLS · XLSX ›** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `home.p-presentations-pptx` — **P Presentations PPTX ›** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `home.pdf-pdf-workspace-pdf` — **PDF PDF Workspace PDF ›** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `home.txt-plain-text-txt` — **TXT Plain Text TXT ›** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `home.epub-epub-reader-epub` — **EPUB EPUB Reader EPUB ›** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `home.openanydocument` — **Open file** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [ ] `home.source` — **Source** — dedicated behavioral confirmation pending
- [ ] `home.status` — **Status** — dedicated behavioral confirmation pending
- [ ] `home.limitations` — **Limitations** — dedicated behavioral confirmation pending
- [ ] `home.contribute` — **Contribute** — dedicated behavioral confirmation pending

### Documents

- [ ] `documents.return-to-inkdesk-home` — **Return to InkDesk home** — dedicated behavioral confirmation pending
- [x] `documents.newbtn` — **New document** — tests/browser/revalidate_docx_three_eras.py; tests/browser/revalidate_v0202_local_recovery.py
- [ ] `documents.open-document` — **Open document** — dedicated behavioral confirmation pending
- [ ] `documents.undobtn` — **Undo** — dedicated behavioral confirmation pending
- [ ] `documents.redobtn` — **Redo** — dedicated behavioral confirmation pending
- [ ] `documents.sidebarbtn` — **Toggle sidebar** — dedicated behavioral confirmation pending
- [ ] `documents.titletext` — **Document name** — dedicated behavioral confirmation pending
- [ ] `documents.zoomout` — **Zoom out** — dedicated behavioral confirmation pending
- [ ] `documents.zoomlabel` — **Reset zoom** — dedicated behavioral confirmation pending
- [ ] `documents.zoomin` — **Zoom in** — dedicated behavioral confirmation pending
- [ ] `documents.fitwidth` — **Fit width** — dedicated behavioral confirmation pending
- [x] `documents.savebtn` — **Save** — tests/browser/revalidate_docx_three_eras.py; tests/browser/revalidate_v0202_local_recovery.py
- [ ] `documents.styleselect` — **Paragraph style** — dedicated behavioral confirmation pending
- [ ] `documents.fontselect` — **Font** — dedicated behavioral confirmation pending
- [ ] `documents.sizeselect` — **Font size** — dedicated behavioral confirmation pending
- [ ] `documents.linespacing` — **Line spacing** — dedicated behavioral confirmation pending
- [ ] `documents.bold` — **Bold** — dedicated behavioral confirmation pending
- [ ] `documents.italic` — **I** — dedicated behavioral confirmation pending
- [ ] `documents.underline` — **U** — dedicated behavioral confirmation pending
- [ ] `documents.justifyleft` — **≡** — dedicated behavioral confirmation pending
- [ ] `documents.justifycenter` — **≣** — dedicated behavioral confirmation pending
- [ ] `documents.justifyright` — **≡** — dedicated behavioral confirmation pending
- [ ] `documents.justifyfull` — **☰** — dedicated behavioral confirmation pending
- [ ] `documents.insertunorderedlist` — **• List** — dedicated behavioral confirmation pending
- [ ] `documents.insertorderedlist` — **1. List** — dedicated behavioral confirmation pending
- [ ] `documents.alphalist` — **A. List** — dedicated behavioral confirmation pending
- [ ] `documents.tablebtn` — **Table** — dedicated behavioral confirmation pending
- [ ] `documents.rowbtn` — **Add table row** — dedicated behavioral confirmation pending
- [ ] `documents.colbtn` — **Add table column** — dedicated behavioral confirmation pending
- [ ] `documents.image` — **Image** — dedicated behavioral confirmation pending
- [ ] `documents.pagespanel` — **Pages** — dedicated behavioral confirmation pending
- [ ] `documents.outlinepanel` — **Outline** — dedicated behavioral confirmation pending
- [ ] `documents.searchpanel` — **Search** — dedicated behavioral confirmation pending
- [ ] `documents.searchinput` — **searchInput** — dedicated behavioral confirmation pending
- [ ] `documents.prevhit` — **↑** — dedicated behavioral confirmation pending
- [ ] `documents.nexthit` — **↓** — dedicated behavioral confirmation pending
- [x] `documents.newwelcomebtn` — **+ New document** — tests/browser/revalidate_docx_three_eras.py; tests/browser/revalidate_v0202_local_recovery.py
- [ ] `documents.open-document-2` — **Open document** — dedicated behavioral confirmation pending

### Spreadsheets

- [ ] `spreadsheets.return-to-inkdesk-home` — **Return to InkDesk home** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.newbtn` — **New workbook** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.openbtn` — **Open workbook** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.undobtn` — **Undo** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.redobtn` — **Redo** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.savebtn` — **Save XLSX copy** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.fontfamily` — **Font** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.fontsize` — **Font size** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.boldbtn` — **Bold** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.italicbtn` — **Italic** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.underlinebtn` — **Underline** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.alignleftbtn` — **Align left** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.aligncenterbtn` — **Align center** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.alignrightbtn` — **Align right** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.mergebtn` — **Merge or unmerge selected cells** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.addrowbtn` — **Insert row below** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.addcolbtn` — **Insert column right** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.deletebtn` — **Clear selected cells** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.deleterowbtn` — **Delete selected rows** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.deletecolbtn` — **Delete selected columns** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.operationselect` — **Operations** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.gridmode` — **Sheet** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.formmode` — **Page** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.gridlinesbtn` — **Show or hide gridlines** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.namebox` — **Cell reference** — dedicated behavioral confirmation pending
- [x] `spreadsheets.formulainput` — **Formula bar** — tests/test_spreadsheet_formula_editor.py; tests/test_spreadsheet_formula_references.py; tests/browser/revalidate_v0201_consistency.py
- [ ] `spreadsheets.newemptybtn` — **+ New Spreadsheet** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.openemptybtn` — **Open Spreadsheet** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.zoomout` — **Zoom out** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.zoomslider` — **Zoom** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.zoomin` — **Zoom in** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.fitwidth` — **Fit width** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.downloadbtn` — **Save XLSX copy** — dedicated behavioral confirmation pending
- [ ] `spreadsheets.closesavebtn` — **Cancel** — dedicated behavioral confirmation pending

### Presentations

- [x] `presentations.return-to-inkdesk-home` — **Return to InkDesk home** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.newbtn` — **+ New Presentation** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.openbtn` — **Open Presentation** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.return-to-inkdesk-home-2` — **Return to InkDesk home** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.newsmall` — **New Presentation** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.opensmall` — **Open Presentation** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.undobtn` — **Undo** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.redobtn` — **Redo** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.presentfromstarttop` — **Present from first slide** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.presentfromcurrenttop` — **Present from current slide** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.savebtn` — **Save PPTX copy** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.home` — **Home** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.insert` — **Insert** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.arrange` — **Arrange** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.view` — **View** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.present` — **Present** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.addslidebtn` — **New slide ▾** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.dupslidebtn` — **Duplicate** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.delslidebtn` — **Delete** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.fontfamily` — **Arial Aptos Calibri Georgia Helvetica Times New Roman** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.fontsize` — **12 16 20 24 32 44 60** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.boldbtn` — **B** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.italicbtn` — **I** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.alignleft` — **⇤** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.aligncenter` — **≡** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.alignright` — **⇥** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.inserttextbtn` — **Text** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.insertimagebtn` — **Image** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.shapetype` — **Shape type** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.insertshapebtn` — **Insert shape** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.frontbtn` — **Bring front** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.backbtn` — **Send back** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.deleteobjbtn` — **Delete object** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.togglepresentationsbtn` — **Hide thumbnails** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.toggleinspectorbtn` — **Show format panel** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.togglenotesbtn` — **Show presenter notes** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.presentviewbtn` — **Present current** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.zoomoutbtn` — **−** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.zoomrange` — **zoomRange** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.zoominbtn` — **+** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.fitbtn` — **Fit** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.transitiontype` — **None Fade Slide Zoom** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.presentfromstartbtn` — **From first slide** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.presentfromcurrentbtn` — **From current slide** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.propx` — **propX** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.propy` — **propY** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.propw` — **propW** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.proph` — **propH** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.propopacity` — **propOpacity** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.propfill` — **propFill** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.proprotation` — **propRotation** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.cropzoom` — **cropZoom** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.cropx` — **cropX** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.cropy` — **cropY** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.resetcropbtn` — **Reset crop** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.presenternotes` — **presenterNotes** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.bottomzoomoutbtn` — **Zoom out** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.bottomzoomrange` — **Zoom level** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.bottomzoominbtn` — **Zoom in** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.bottomfitbtn` — **Fit slide** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.exitpresentbtn` — **Exit presentation** — tests/browser/revalidate_presentations_controls.py
- [x] `presentations.closetemplatebtn` — **Close** — tests/browser/revalidate_presentations_controls.py

### Pdf

- [ ] `pdf.return-to-inkdesk-home` — **Return to InkDesk home** — dedicated behavioral confirmation pending
- [ ] `pdf.openbtn` — **Open PDF** — dedicated behavioral confirmation pending
- [ ] `pdf.inkdesk-home` — **InkDesk home** — dedicated behavioral confirmation pending
- [ ] `pdf.opensmall` — **Open PDF** — dedicated behavioral confirmation pending
- [ ] `pdf.sidebartoggle` — **Toggle navigation panel** — dedicated behavioral confirmation pending
- [ ] `pdf.savemodifiedpdfbtn` — **Save annotated PDF** — dedicated behavioral confirmation pending
- [ ] `pdf.fullscreenbtn` — **Full screen** — dedicated behavioral confirmation pending
- [ ] `pdf.systemopenbtn` — **Open in system viewer** — dedicated behavioral confirmation pending
- [ ] `pdf.prevpage` — **Previous page** — dedicated behavioral confirmation pending
- [ ] `pdf.pagenumber` — **Page number** — dedicated behavioral confirmation pending
- [ ] `pdf.nextpage` — **Next page** — dedicated behavioral confirmation pending
- [ ] `pdf.zoomout` — **Zoom out** — dedicated behavioral confirmation pending
- [ ] `pdf.zoomselect` — **Zoom** — dedicated behavioral confirmation pending
- [ ] `pdf.zoomin` — **Zoom in** — dedicated behavioral confirmation pending
- [ ] `pdf.verticalscroll` — **Continuous vertical scrolling** — dedicated behavioral confirmation pending
- [ ] `pdf.horizontalscroll` — **Horizontal document scrolling** — dedicated behavioral confirmation pending
- [ ] `pdf.select` — **Select PDF text or fill AcroForm fields** — dedicated behavioral confirmation pending
- [ ] `pdf.highlight` — **Highlight selected text** — dedicated behavioral confirmation pending
- [ ] `pdf.underline` — **Underline selected text** — dedicated behavioral confirmation pending
- [ ] `pdf.marker` — **Free marker area** — dedicated behavioral confirmation pending
- [ ] `pdf.comment` — **Comment on selected text** — dedicated behavioral confirmation pending
- [ ] `pdf.text` — **Insert free text** — dedicated behavioral confirmation pending
- [ ] `pdf.undoreview` — **Undo last review action** — dedicated behavioral confirmation pending
- [ ] `pdf.bookmarkbtn` — **Add or remove bookmark** — dedicated behavioral confirmation pending
- [ ] `pdf.pages` — **Pages** — dedicated behavioral confirmation pending
- [ ] `pdf.outline` — **Index** — dedicated behavioral confirmation pending
- [ ] `pdf.bookmarks` — **Bookmarks** — dedicated behavioral confirmation pending
- [ ] `pdf.comments` — **Comments** — dedicated behavioral confirmation pending
- [ ] `pdf.immersiveexit` — **Exit full screen** — dedicated behavioral confirmation pending
- [ ] `pdf.textdialogvalue` — **textDialogValue** — dedicated behavioral confirmation pending
- [ ] `pdf.dialogcancel` — **Cancel** — dedicated behavioral confirmation pending
- [ ] `pdf.insert` — **Insert** — dedicated behavioral confirmation pending

### Txt

- [ ] `txt.inkdesk-home` — **InkDesk home** — dedicated behavioral confirmation pending
- [x] `txt.newbtn` — **New text file** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- [x] `txt.openbtn` — **Open text file** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- [ ] `txt.undobtn` — **Undo** — dedicated behavioral confirmation pending
- [ ] `txt.redobtn` — **Redo** — dedicated behavioral confirmation pending
- [ ] `txt.doctitle` — **Text file name** — dedicated behavioral confirmation pending
- [x] `txt.savebtn` — **Save text file** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- [x] `txt.wrapbtn` — **Wrap** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- [ ] `txt.fontsize` — **Text size** — dedicated behavioral confirmation pending
- [x] `txt.findbtn` — **Find** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- [ ] `txt.findinput` — **Find text** — dedicated behavioral confirmation pending
- [x] `txt.findprevious` — **Previous result** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- [x] `txt.findnext` — **Next result** — tests/test_txt_module.py; tests/browser/revalidate_cross_workspace_isolation.py
- [ ] `txt.findclose` — **Close find** — dedicated behavioral confirmation pending
- [ ] `txt.newstartbtn` — **New text file** — dedicated behavioral confirmation pending
- [ ] `txt.openstartbtn` — **Open text file** — dedicated behavioral confirmation pending
- [ ] `txt.editor` — **Plain text editor** — dedicated behavioral confirmation pending

### Epub

- [ ] `epub.inkdesk-home` — **InkDesk home** — dedicated behavioral confirmation pending
- [x] `epub.openbtn` — **Open EPUB** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `epub.tocbtn` — **Table of contents** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [ ] `epub.doctitle` — **EPUB file name** — dedicated behavioral confirmation pending
- [ ] `epub.savebtn` — **Save renamed EPUB copy** — dedicated behavioral confirmation pending
- [x] `epub.fontdecrease` — **Decrease text size** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `epub.fontincrease` — **Increase text size** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [ ] `epub.paper` — **Paper theme** — dedicated behavioral confirmation pending
- [ ] `epub.sepia` — **Sepia theme** — dedicated behavioral confirmation pending
- [ ] `epub.sage` — **Sage theme** — dedicated behavioral confirmation pending
- [ ] `epub.night` — **Night theme** — dedicated behavioral confirmation pending
- [ ] `epub.tocclose` — **Close contents** — dedicated behavioral confirmation pending
- [ ] `epub.openstartbtn` — **Open EPUB** — dedicated behavioral confirmation pending
- [x] `epub.previouspage` — **Previous page** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py
- [x] `epub.nextpage` — **Next page** — tests/browser/revalidate_cross_workspace_isolation.py; tests/browser/revalidate_launch_and_offline_modes.py



### Presentations panel acceptance clarification — correction 4

The Format panel and Presenter Notes are intentionally **collapsed when a presentation is opened**.
Passing acceptance requires the View controls to open them, the controls inside the Format panel to change the selected object, and the same controls to close/reopen the panels without losing state. A hidden initial panel is therefore not a failure; an unresponsive Show button is.


### Presentations state-machine correction — correction 5

The Format panel now has one JavaScript source of truth (`inspectorOpen`). Desktop and compact CSS classes are derived from that value instead of being toggled independently. A fresh compact/iPad-width presentation must start collapsed, remove the desktop-only `hide-inspector` class, open through **Show format panel**, report matching `aria-expanded`, close with Escape, and stay synchronized across breakpoint changes. This directly covers the cold-start path that was previously missing.


### Presentations state simplification — correction 6

The Format panel now keeps the same canonical classes at every viewport width: `inspector-open` means open and `hide-inspector` means closed. Resizing or rotating changes only the CSS layout (desktop sidebar versus compact fixed drawer); JavaScript no longer tries to close or translate state during the breakpoint transition. This removes the asynchronous `matchMedia`/`requestAnimationFrame` race seen in hosted Chromium. Acceptance now requires an open desktop panel to remain logically and visually open after switching to compact width, followed by a successful close, reopen, and Escape close. Fresh compact starts still begin collapsed.
