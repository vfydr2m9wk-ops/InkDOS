from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PdfReviewModularizationTests(unittest.TestCase):
    def test_review_boundary_is_explicit_precached_and_ratcheted(self):
        app = (ROOT / "apps/pdf/app.js").read_text(encoding="utf-8")
        controller_path = ROOT / "apps/pdf/review/review-controller.js"
        layer_path = ROOT / "apps/pdf/review/annotation-layer.js"
        controller = controller_path.read_text(encoding="utf-8")
        layer = layer_path.read_text(encoding="utf-8")
        html = (ROOT / "apps/pdf/index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))

        self.assertTrue(controller_path.is_file())
        self.assertTrue(layer_path.is_file())
        self.assertLessEqual(len(controller.splitlines()), 500)
        self.assertLessEqual(len(layer.splitlines()), 500)
        self.assertTrue(all(len(line) <= 240 for line in controller.splitlines()))
        self.assertTrue(all(len(line) <= 240 for line in layer.splitlines()))
        self.assertIn("window.InkDeskPdfReviewController.createReviewController", app)
        self.assertNotIn("function applyTextSelection(", app)
        self.assertNotIn("function renderPageReview(", app)
        self.assertNotIn("function wireReviewLayer(", app)
        self.assertNotIn("function undoLastReviewAction(", app)
        self.assertNotIn("function saveReview()", app)
        self.assertIn("review/annotation-layer.js?v=0.20.2.26", html)
        self.assertIn("review/review-controller.js?v=0.20.2.26", html)
        self.assertLess(
            html.index("review/annotation-layer.js?v=0.20.2.26"),
            html.index("review/review-controller.js?v=0.20.2.26"),
        )
        self.assertLess(
            html.index("review/review-controller.js?v=0.20.2.26"),
            html.index("viewer/page-renderer.js?v=0.20.2.26"),
        )
        self.assertIn("'./apps/pdf/review/annotation-layer.js'", worker)
        self.assertIn("'./apps/pdf/review/review-controller.js'", worker)
        self.assertLessEqual(len(app.splitlines()), 500)
        self.assertNotIn("apps/pdf/app.js", policy["grandfatheredDebt"])
        self.assertNotIn("apps/pdf/review/review-controller.js", policy["grandfatheredDebt"])
        self.assertNotIn("apps/pdf/review/annotation-layer.js", policy["grandfatheredDebt"])


if __name__ == "__main__":
    unittest.main()
