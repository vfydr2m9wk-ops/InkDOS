from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_pdf_bootstrap_composes_dedicated_persistent_annotation_modes():
    app = read("apps/pdf/app.js")
    module = read("apps/pdf/ui/annotation-modes.js")
    assert "ui/annotation-modes.js" in app
    assert "NS.AnnotationModes.create" in app
    assert "NS.AnnotationModes=Object.freeze({create})" in module


def test_pdf_persistent_modes_keep_highlight_note_delete_armed():
    module = read("apps/pdf/ui/annotation-modes.js")
    assert "['none','highlight','note','delete']" in module
    assert "Highlight mode armed" in module
    assert "Note mode armed" in module
    assert "Delete annotation mode armed" in module
    assert "document.addEventListener('selectionchange'" in module


def test_pdf_highlight_mode_has_persistent_color_palette():
    module = read("apps/pdf/ui/annotation-modes.js")
    assert "highlightColor" in module
    assert "data-pdf-highlight-color" in module
    assert "setHighlightColor" in module
    assert "border-radius:50%" in module


def test_pdf_note_mode_reuses_review_annotation_comment_store():
    module = read("apps/pdf/ui/annotation-modes.js")
    review = read("apps/pdf/extensions/review-annotations.js")
    assert "openComment" in module
    assert "extensions.openComment()" in module
    assert "saveComment" in review
    assert "executeAdd(item,'Comment added')" in review


def test_pdf_delete_mode_removes_extension_annotations_intersecting_selection():
    module = read("apps/pdf/ui/annotation-modes.js")
    review = read("apps/pdf/extensions/review-annotations.js")
    assert "deleteSelectedAnnotations" in module
    assert "extensions.deleteSelection" in module
    assert "deleteSelection" in review
    assert "No saved annotation overlaps this selection." in module
