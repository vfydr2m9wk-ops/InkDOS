from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PdfTextboxBaselineTests(unittest.TestCase):
    def test_pdf_loads_shared_workspace_baseline(self):
        index = (ROOT / "apps" / "pdf" / "index.html").read_text(encoding="utf-8")
        self.assertIn("shared/ui/workspace-layout.css", index)
        self.assertIn("shared/ui/workspace-panel-controller.js", index)
        self.assertIn("shared/ui/workspace-layout.js", index)
        self.assertEqual(index.count("shared/file-router.js"), 1)

    def test_text_box_uses_app_dialog_instead_of_annotation_prompt(self):
        annotation = (
            ROOT / "apps" / "pdf" / "review" / "annotation-layer.js"
        ).read_text(encoding="utf-8")
        controller = (
            ROOT / "apps" / "pdf" / "review" / "review-controller.js"
        ).read_text(encoding="utf-8")

        self.assertNotIn("prompt('Text:'", annotation)
        self.assertIn("requestTextAnnotation", annotation)
        self.assertIn("requestTextEdit", annotation)
        self.assertIn("textDialogForm", controller)
        self.assertIn("annotation-update", controller)
        self.assertIn("Text box inserted.", controller)
        self.assertIn("Text box updated.", controller)

    def test_review_state_mutation_is_owned_by_controller(self):
        annotation = (
            ROOT / "apps" / "pdf" / "review" / "annotation-layer.js"
        ).read_text(encoding="utf-8")
        controller = (
            ROOT / "apps" / "pdf" / "review" / "review-controller.js"
        ).read_text(encoding="utf-8")

        self.assertNotIn("state.annotations.push", annotation)
        self.assertNotIn("state.undo.push", annotation)
        self.assertIn("function commitFreeAnnotation", controller)
        self.assertIn("state.annotations.push(annotation)", controller)
        self.assertIn("state.undo.push", controller)


if __name__ == "__main__":
    unittest.main()
