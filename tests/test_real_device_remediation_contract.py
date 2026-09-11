from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pdf_virtualization_reserves_geometry_and_preserves_anchor():
    source = read("apps/pdf/view/page-layout.js")
    assert "reserveGeometry" in source
    assert "captureAnchor" in source
    assert "restoreAnchor" in source
    assert "userScrollEpoch" in source
    assert "policy.cssHeight" in source
    assert "userScrollingUntil" in source
    assert "deferTrim" in source
    assert "if(this.isUserScrolling())this.deferTrim()" in source
    assert "touchmove" in source


def test_docx_explicit_false_page_break_is_not_promoted_to_hard_break():
    app = read("apps/documents/app.js")
    assert "installDocxBooleanCompatibility" in app
    assert "falseValues=new Set(['0','false','off','no'])" in app
    assert "pageBreakBefore" in app
    assert "block.hardPageBreakBefore=false" in app
    assert "installDocxBooleanCompatibility();await loadD1()" in app


def test_txt_save_cleans_exact_revision_and_dirty_exit_is_three_way():
    session = read("apps/txt/runtime/contracts/document-session.js")
    io = read("apps/txt/io/txt-file-controller.js")
    controls = read("apps/txt/ui/txt-controls.js")
    assert "if(rev===this.revision)this.dirty=false" in session
    assert "saveForReplacement" in io and "authorizeReplacement" in io
    assert "choice==='save'" in io and "choice==='discard'" in io and "choice==='clean'" in io
    assert "snap.revision===state.session.revision&&!state.session.dirty" in io
    assert "discardSave" in controls and "files.resolveDiscard('save')" in controls
    assert "files.resolveDiscard('discard')" in controls and "files.resolveDiscard('cancel')" in controls
    assert "files.authorizeReplacement('Save changes before returning to InkDOS Home?')" in controls
    assert "beforeunload" in controls


def test_epub_dirty_annotations_gate_open_home_and_leave_until_save_finishes():
    controls = read("apps/epub/ui/reader-controls.js")
    bindings = read("apps/epub/ui/reader-bindings.js")
    assert "hasUnsavedEdits" in controls
    assert "saveForLeave" in controls and "requestLeave" in controls
    assert "choice==='save'" in controls and "choice==='discard'" in controls and "choice==='clean'" in controls
    assert "savedAnnotationRevision" in controls
    assert "revision!==state.annotationRevision" in controls
    assert "state.book&&hasUnsavedEdits()&&!(await requestLeave())" in controls
    assert "reader.hasUnsavedEdits()" in bindings
    assert "await reader.requestLeave()" in bindings
    assert "beforeunload" in bindings


def test_epub_selection_exposes_highlight_and_note_actions():
    bindings = read("apps/epub/ui/reader-bindings.js")
    controls = read("apps/epub/ui/reader-controls.js")
    css = read("apps/epub/ui/reader-controls.css")
    assert "epub-selection-actions" in bindings
    assert "Highlight" in bindings and "Note" in bindings
    assert "openHighlightForSelection" in bindings
    assert "addNoteFromSelection" in bindings
    assert "function openHighlightForSelection" in controls
    assert "function addNoteFromSelection" in controls
    assert ".epub-selection-actions" in css


def test_spreadsheet_color_fidelity_handles_theme_indexed_tint_and_tables():
    source = read("apps/spreadsheets/io/xlsx-color-fidelity.js")
    opener = read("apps/spreadsheets/io/file-open-controller.js")
    sw = read("service-worker.js")
    assert "THEME_ORDER=['lt1','dk1','lt2','dk2'" in source
    assert "indexed" in source and "tint" in source and "theme" in source
    assert "applyTableStyles" in source and "tablePalette" in source
    assert "xlsx-color-fidelity.js" in opener
    assert "./apps/spreadsheets/io/xlsx-color-fidelity.js" in sw


def test_txt_large_file_mode_avoids_full_history_and_recovery_snapshots():
    io = read("apps/txt/io/txt-file-controller.js")
    editor = read("apps/txt/editor/editor-controller.js")
    assert "MAX_BYTES=64*1024*1024" in io
    assert "LARGE_BYTES=4*1024*1024" in io
    assert "state.largeFile" in io
    assert "if(!state.loaded||state.largeFile)return false" in io
    assert "if(!state.largeFile)state.history.push" in editor
    assert "recovery paused" in editor
    assert "large-file mode" in editor


def test_legacy_ppt_has_fidelity_and_editable_copy_path():
    reader = read("apps/presentations/io/ppt-legacy-reader.js")
    save = read("apps/presentations/io/save-controller.js")
    commands = read("apps/presentations/ui/command-controller.js")
    assert "props[0x01c0]" in reader
    assert "resolvedShape==='line'" in reader
    assert "textObject({...anchor,rotation,text" in reader and "fill,line" in reader
    assert "legacy-ppt-to-editable-pptx" in save
    assert "replace(/\\.ppt$/i,'.pptx')" in save
    assert "Legacy PowerPoint (.ppt) opened read-only" in commands
    assert "Save editable PPTX copy" in commands


def test_legacy_ppt_save_promotes_confirmed_copy_into_editable_session():
    save = read("apps/presentations/io/save-controller.js")
    app = read("apps/presentations/app.js")
    assert "promoteLegacyPpt" in save
    assert "await promoteLegacyPpt({bytes,fileName,receipt})" in save
    assert "sourceKind==='ppt'" in save
    assert "SaveController.create({session,chrome,promoteLegacyPpt:" in app
    assert "fileOpen.openFile(new File([bytes],fileName" in app
    assert "open the .pptx copy to edit" not in save


def test_pptx_text_style_cascade_uses_placeholder_fallbacks():
    source = read("apps/presentations/io/pptx-open-controller.js")
    assert "function runStyle(rPr,def,theme,map,fallback={})" in source
    assert "fallback.fontSizePt" in source
    assert "fallback.fontFamily" in source
    assert "fallback.color" in source
    assert "function bodyInfo(txBody,fallback={})" in source
    assert "...bodyInfo(tx,inherit||{})" in source


def test_pptx_normal_autofit_preserves_line_spacing_reduction_when_text_is_rewritten():
    writer = read("apps/presentations/io/pptx-preservation-writer.js")
    assert "const priorNorm=child(body,'normAutofit')" in writer
    assert "attr(priorNorm,'lnSpcReduction','0')" in writer
    assert "n.setAttribute('lnSpcReduction',lineSpacingReduction)" in writer


if __name__ == "__main__":
    test_legacy_ppt_save_promotes_confirmed_copy_into_editable_session()
