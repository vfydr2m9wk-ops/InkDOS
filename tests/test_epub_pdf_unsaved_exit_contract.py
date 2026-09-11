from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPUB_BINDINGS = (ROOT / "apps/epub/ui/reader-bindings.js").read_text()
EPUB_CONTROLS = (ROOT / "apps/epub/ui/reader-controls.js").read_text()
EPUB_SESSION = (ROOT / "apps/epub/session/book-session.js").read_text()
PDF_COMMANDS = (ROOT / "apps/pdf/ui/command-controller.js").read_text()
PDF_SAVE = (ROOT / "apps/pdf/io/save-controller.js").read_text()


def test_epub_guards_dirty_open_home_and_browser_unload():
    assert "authorizeReplacement" in EPUB_CONTROLS
    assert "saveForReplacement" in EPUB_CONTROLS
    assert "decision==='save'" in EPUB_CONTROLS
    assert "decision==='discard'" in EPUB_CONTROLS
    assert "decision==='cancel'" in EPUB_CONTROLS
    assert "a[aria-label=\"Home\"]" in EPUB_BINDINGS
    assert "beforeunload" in EPUB_BINDINGS
    assert "reader.requestOpen" in EPUB_BINDINGS


def test_epub_replacement_save_is_revision_aware_and_can_mark_clean():
    assert "const revision=state.annotationRevision" in EPUB_CONTROLS
    assert "state.annotationRevision!==revision" in EPUB_CONTROLS
    assert "session.markSaved(revision)" in EPUB_CONTROLS
    assert "function markSaved(revision)" in EPUB_SESSION


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
