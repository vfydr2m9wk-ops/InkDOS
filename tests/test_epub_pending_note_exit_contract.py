from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps/epub/app.js").read_text(encoding="utf-8")
MODES = (ROOT / "apps/epub/ui/annotation-modes.js").read_text(encoding="utf-8")
BINDINGS = (ROOT / "apps/epub/ui/reader-bindings.js").read_text(encoding="utf-8")


def test_epub_note_draft_participates_in_dirty_exit_contract():
    assert "annotationModes" in APP
    assert "ReaderBindings.create({elements:E,reader:controls.api,navigation:navigation.api,annotationModes})" in APP
    assert "hasPendingNoteDraft" in MODES
    assert "commitPendingNote" in MODES
    assert "discardPendingNote" in MODES
    assert "annotationModes?.hasPendingNoteDraft()" in BINDINGS


def test_epub_save_discard_cancel_preserve_note_draft_semantics():
    assert "annotationModes?.commitPendingNote()" in BINDINGS
    assert "annotationModes?.discardPendingNote()" in BINDINGS
    assert "decision==='discard'" in BINDINGS
    assert "decision==='cancel'" in BINDINGS
    assert "decision==='save'" in BINDINGS
    assert "beforeunload" in BINDINGS
