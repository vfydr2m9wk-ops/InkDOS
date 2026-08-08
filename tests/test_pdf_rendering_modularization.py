from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PdfRenderingModularizationTests(unittest.TestCase):
    def test_page_renderer_boundary_is_explicit_and_cached(self):
        app = (ROOT / "apps/pdf/app.js").read_text(encoding="utf-8")
        renderer_path = ROOT / "apps/pdf/viewer/page-renderer.js"
        renderer = renderer_path.read_text(encoding="utf-8")
        html = (ROOT / "apps/pdf/index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))

        self.assertTrue(renderer_path.is_file())
        self.assertLessEqual(len(renderer.splitlines()), 500)
        self.assertTrue(all(len(line) <= 240 for line in renderer.splitlines()))
        self.assertIn("window.InkDeskPdfPageRenderer.createPageRenderer", app)
        self.assertNotIn("function pageScale(base)", app)
        self.assertNotIn("async function renderPage(pageNumber)", app)
        self.assertNotIn("function observePages()", app)
        self.assertIn("viewer/page-renderer.js?v=0.20.2.28", html)
        self.assertLess(
            html.index("viewer/page-renderer.js?v=0.20.2.28"),
            html.index("app.js?v=0.20.2.28"),
        )
        self.assertIn("'./apps/pdf/viewer/page-renderer.js'", worker)
        self.assertLessEqual(len(app.splitlines()), 500)
        self.assertNotIn("apps/pdf/app.js", policy["grandfatheredDebt"])
        self.assertNotIn("apps/pdf/viewer/page-renderer.js", policy["grandfatheredDebt"])


if __name__ == "__main__":
    unittest.main()
