from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_epub_uses_persistent_annotation_modes_instead_of_selection_first_bubble():
    app = read("apps/epub/app.js")
    assert "installAnnotationModes" in app
    assert "['none','highlight','note','delete']" in app
    assert "Highlight mode armed" in app
    assert "Note mode armed" in app
    assert "Delete annotation mode armed" in app
    assert "document.querySelector('.epub-selection-actions')?.remove()" in app
    assert "document.addEventListener('selectionchange'" in app


def test_epub_highlight_color_stays_armed_and_palette_is_color_only():
    app = read("apps/epub/app.js")
    assert "elements.highlightBtn.dataset.highlightColor=color" in app
    assert "button.dataset.highlightColor===color" in app
    assert '.highlight-choice>span:last-child{display:none!important}' in app
    assert '.highlight-swatch{width:28px;height:28px;border-radius:50%}' in app


def test_epub_note_mode_uses_compact_in_app_editor_and_existing_annotation_store():
    app = read("apps/epub/app.js")
    assert "epub-note-dialog" in app
    assert "session.addNote({...input,text})" in app
    assert "session.persist()" in app
    assert "reader.prepareExport()" in app
    assert "reader.addNoteFromSelection" not in app


def test_epub_delete_mode_removes_overlapping_highlights_and_notes():
    app = read("apps/epub/app.js")
    assert "deleteSelectedAnnotations" in app
    assert "session.removeNote(id)" in app
    assert "reader.removeHighlight()" in app
    assert "No saved annotation overlaps this selection." in app


def test_epub_contents_is_icon_only_with_existing_accessible_name():
    app = read("apps/epub/app.js")
    index = read("apps/epub/index.html")
    assert '#tocBtn>span{display:none!important}' in app
    assert 'id="tocBtn"' in index
    assert 'aria-label="Contents"' in index
