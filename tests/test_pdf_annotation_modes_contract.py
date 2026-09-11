import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class PdfAnnotationModesContractTests(unittest.TestCase):
    def test_pdf_bootstrap_composes_dedicated_persistent_annotation_modes(self):
        app = read("apps/pdf/app.js")
        module = read("apps/pdf/ui/annotation-modes.js")
        self.assertIn("ui/annotation-modes.js", app)
        self.assertIn("NS.AnnotationModes.create", app)
        self.assertIn("NS.AnnotationModes=Object.freeze({create})", module)

    def test_pdf_persistent_modes_keep_highlight_note_delete_armed(self):
        module = read("apps/pdf/ui/annotation-modes.js")
        self.assertIn("['none','highlight','note','delete']", module)
        self.assertIn("Highlight mode armed", module)
        self.assertIn("Note mode armed", module)
        self.assertIn("Delete annotation mode armed", module)
        self.assertIn("document.addEventListener('selectionchange'", module)

    def test_pdf_highlight_mode_has_persistent_color_palette(self):
        module = read("apps/pdf/ui/annotation-modes.js")
        self.assertIn("highlightColor", module)
        self.assertIn("data-pdf-highlight-color", module)
        self.assertIn("setHighlightColor", module)
        self.assertIn("border-radius:50%", module)
        self.assertIn("item.record.color=hexColor(highlightColor)", module)

    def test_pdf_note_mode_reuses_review_annotation_comment_store(self):
        module = read("apps/pdf/ui/annotation-modes.js")
        review = read("apps/pdf/extensions/review-annotations.js")
        self.assertIn("openComment", module)
        self.assertIn("extensions.openComment()", module)
        self.assertIn("saveComment", review)
        self.assertIn("executeAdd(item,'Comment added')", review)

    def test_pdf_delete_mode_removes_extension_annotations_intersecting_selection(self):
        module = read("apps/pdf/ui/annotation-modes.js")
        self.assertIn("deleteSelectedAnnotations", module)
        self.assertIn("extensions.doc.annotationStorage", module)
        self.assertIn("extensions.editor.addCommand", module)
        self.assertIn("storage.remove(item.key)", module)
        self.assertIn("No saved annotation overlaps this selection.", module)


if __name__ == "__main__":
    unittest.main()
