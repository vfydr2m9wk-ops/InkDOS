import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class PdfAnnotationModesContractTests(unittest.TestCase):
    def test_pdf_bootstrap_composes_persistent_annotation_modes_from_cached_mode_layer(self):
        app = read("apps/pdf/app.js")
        module = read("apps/pdf/ui/mode-bindings.js")
        self.assertIn("ui/mode-bindings.js", app)
        self.assertIn("NS.AnnotationModes.create", app)
        self.assertIn("NS.AnnotationModes=Object.freeze({create:createAnnotationModes})", module)

    def test_pdf_persistent_modes_keep_highlight_note_delete_armed(self):
        module = read("apps/pdf/ui/mode-bindings.js")
        self.assertIn("['none','highlight','note','delete']", module)
        self.assertIn("Highlight mode armed", module)
        self.assertIn("Note mode armed", module)
        self.assertIn("Delete annotation mode armed", module)
        self.assertIn("document.addEventListener('selectionchange'", module)

    def test_pdf_highlight_color_is_integrated_into_icon_and_palette_is_overlay(self):
        module = read("apps/pdf/ui/mode-bindings.js")
        self.assertIn("highlightColor", module)
        self.assertIn("pdfHighlightColor", module)
        self.assertIn("setHighlightColor", module)
        self.assertIn("paletteOpen", module)
        self.assertIn("positionPalette", module)
        self.assertIn("palette.hidden=!paletteOpen", module)
        self.assertIn("highlightBtn.style.setProperty('--pdf-highlight-color',highlightColor)", module)
        self.assertIn("position:fixed", module)
        self.assertIn("#persistentHighlightBtn svg{stroke:var(--pdf-highlight-color)}", module)
        self.assertIn("item.record.color=hexColor(highlightColor)", module)

    def test_pdf_note_mode_reuses_review_annotation_comment_store(self):
        module = read("apps/pdf/ui/mode-bindings.js")
        review = read("apps/pdf/extensions/review-annotations.js")
        self.assertIn("openComment", module)
        self.assertIn("extensions.openComment()", module)
        self.assertIn("saveComment", review)
        self.assertIn("executeAdd(item,'Comment added')", review)

    def test_pdf_delete_mode_removes_extension_annotations_intersecting_selection(self):
        module = read("apps/pdf/ui/mode-bindings.js")
        self.assertIn("deleteSelectedAnnotations", module)
        self.assertIn("extensions.doc.annotationStorage", module)
        self.assertIn("extensions.editor.addCommand", module)
        self.assertIn("storage.remove(item.key)", module)
        self.assertIn("No saved annotation overlaps this selection.", module)


if __name__ == "__main__":
    unittest.main()
