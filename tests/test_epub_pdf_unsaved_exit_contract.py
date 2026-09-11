from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPUB_APP = (ROOT / "apps/epub/app.js").read_text()
EPUB_MODES = (ROOT / "apps/epub/ui/annotation-modes.js").read_text()
EPUB_BINDINGS = (ROOT / "apps/epub/ui/reader-bindings.js").read_text()
PDF_COMMANDS = (ROOT / "apps/pdf/ui/command-controller.js").read_text()
PDF_SAVE = (ROOT / "apps/pdf/io/save-controller.js").read_text()


def test_epub_guards_dirty_open_home_and_browser_unload():
    assert "authorizeReplacement" in EPUB_BINDINGS
    assert "if(!dirty())return true" in EPUB_BINDINGS
    assert "saveForReplacement" in EPUB_BINDINGS
    assert "decision==='save'" in EPUB_BINDINGS
    assert "decision==='discard'" in EPUB_BINDINGS
    assert "decision==='cancel'" in EPUB_BINDINGS
    assert "a[aria-label=\"Home\"]" in EPUB_BINDINGS
    assert "beforeunload" in EPUB_BINDINGS
    assert "requestOpen" in EPUB_BINDINGS


def test_epub_replacement_save_is_revision_aware():
    assert "const revision=ready.annotationRevision" in EPUB_BINDINGS
    assert "after.annotationRevision!==revision" in EPUB_BINDINGS
    assert "await reader.saveCopy()" in EPUB_BINDINGS


def test_epub_pending_note_draft_is_part_of_replacement_authorization():
    assert "ReaderBindings.create({elements:E,reader:controls.api,navigation:navigation.api,annotationModes})" in EPUB_APP
    assert "hasPendingNoteDraft" in EPUB_MODES
    assert "commitPendingNote" in EPUB_MODES
    assert "discardPendingNote" in EPUB_MODES
    assert "annotationModes?.hasPendingNoteDraft()" in EPUB_BINDINGS
    assert "annotationModes.commitPendingNote()" in EPUB_BINDINGS
    assert "annotationModes?.discardPendingNote()" in EPUB_BINDINGS


def test_epub_explicit_save_still_delivers_a_copy_when_clean():
    assert "async function saveCurrentCopy" in EPUB_BINDINGS
    assert "E.save.addEventListener('click',()=>saveCurrentCopy())" in EPUB_BINDINGS
    assert "return await reader.saveCopy()" in EPUB_BINDINGS


def test_pdf_guards_dirty_open_and_home_with_three_way_choice():
    assert "authorizeReplacement" in PDF_COMMANDS
    assert "decision==='save'" in PDF_COMMANDS
    assert "decision==='discard'" in PDF_COMMANDS
    assert "decision==='cancel'" in PDF_COMMANDS
    assert "a[aria-label=\"Home\"]" in PDF_COMMANDS
    assert "await save.saveForReplacement()" in PDF_COMMANDS


def test_pdf_replacement_save_is_snapshot_aware():
    assert "async function saveForReplacement" in PDF_SAVE
    assert "snapshotHash" in PDF_SAVE
    assert "annotationStorage.serializable.hash!==snapshotHash" in PDF_SAVE
