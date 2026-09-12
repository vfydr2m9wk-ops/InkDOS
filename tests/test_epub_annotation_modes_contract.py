from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_epub_bootstrap_composes_dedicated_annotation_mode_module():
    app = read("apps/epub/app.js")
    index = read("apps/epub/index.html")
    module = read("apps/epub/ui/annotation-modes.js")
    assert "NS.AnnotationModes.create" in app
    assert "installAnnotationModes" not in app
    assert "document.createElement('style')" not in app
    assert '<script src="ui/annotation-modes.js"></script>' in index
    assert "NS.AnnotationModes=Object.freeze({create})" in module


def test_epub_uses_persistent_annotation_modes_instead_of_selection_first_bubble():
    module = read("apps/epub/ui/annotation-modes.js")
    assert "['none','highlight','note','delete']" in module
    assert "Highlight mode armed" in module
    assert "Note mode armed" in module
    assert "Delete annotation mode armed" in module
    assert "finalizeLegacySelectionUi" in module
    assert "document.querySelector('.epub-selection-actions')?.remove()" in module
    assert "document.addEventListener('selectionchange'" in module


def test_epub_highlight_color_is_integrated_into_icon_and_palette_does_not_shift_toolbar():
    module = read("apps/epub/ui/annotation-modes.js")
    css = read("apps/epub/ui/reader-controls.css")
    assert "elements.highlightBtn.dataset.highlightColor=color" in module
    assert "button.dataset.highlightColor===color" in module
    assert "positionHighlightPalette" in module
    assert "paletteOpen" in module
    assert "elements.highlight.hidden=!paletteOpen" in module
    assert '#highlightBtn[data-highlight-color]::after' not in css
    assert '#highlightBtn[data-highlight-color="yellow"]{color:#ffe36e}' in css
    assert '.highlight-sheet.compact-color-popover' in css
    assert 'position:fixed' in css
    assert '.highlight-choice>span:last-child{display:none!important}' in css
    assert '.highlight-swatch{width:28px;height:28px;border-radius:50%}' in css


def test_epub_note_mode_uses_compact_in_app_editor_and_existing_annotation_store():
    module = read("apps/epub/ui/annotation-modes.js")
    assert "epub-note-dialog" in module
    assert "session.addNote({...input,text})" in module
    assert "session.persist()" in module
    assert "reader.prepareExport()" in module
    assert "reader.addNoteFromSelection" not in module


def test_epub_delete_mode_removes_overlapping_highlights_and_notes():
    module = read("apps/epub/ui/annotation-modes.js")
    assert "deleteSelectedAnnotations" in module
    assert "session.removeNote(id)" in module
    assert "reader.removeHighlight()" in module
    assert "No saved annotation overlaps this selection." in module


def test_epub_contents_is_icon_only_with_existing_accessible_name():
    css = read("apps/epub/ui/reader-controls.css")
    index = read("apps/epub/index.html")
    assert '#tocBtn>span{display:none!important}' in css
    assert 'id="tocBtn"' in index
    assert 'aria-label="Contents"' in index
