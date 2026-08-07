from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PdfNavigationModularizationTests(unittest.TestCase):
    def test_navigation_boundary_is_explicit_and_precached(self):
        app = (ROOT / "apps/pdf/app.js").read_text(encoding="utf-8")
        controller_path = ROOT / "apps/pdf/viewer/navigation-controller.js"
        controller = controller_path.read_text(encoding="utf-8")
        html = (ROOT / "apps/pdf/index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))

        self.assertTrue(controller_path.is_file())
        self.assertLessEqual(len(controller.splitlines()), 500)
        self.assertTrue(all(len(line) <= 240 for line in controller.splitlines()))
        self.assertIn("window.InkDeskPdfNavigationController.createNavigationController", app)
        self.assertNotIn("function renderThumbnailWindow()", app)
        self.assertNotIn("function renderOutline()", app)
        self.assertNotIn("function navigateToPage(", app)
        self.assertNotIn("querySelectorAll('.sidebar-tab')", app)
        self.assertIn("viewer/navigation-controller.js?v=0.20.2.17", html)
        self.assertLess(
            html.index("viewer/navigation-controller.js?v=0.20.2.17"),
            html.index("viewer/page-renderer.js?v=0.20.2.17"),
        )
        self.assertIn("'./apps/pdf/viewer/navigation-controller.js'", worker)
        self.assertLessEqual(len(app.splitlines()), 500)
        self.assertNotIn("apps/pdf/app.js", policy["grandfatheredDebt"])
        self.assertNotIn("apps/pdf/viewer/navigation-controller.js", policy["grandfatheredDebt"])


if __name__ == "__main__":
    unittest.main()
