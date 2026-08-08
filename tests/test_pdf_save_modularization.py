from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PdfSaveModularizationTests(unittest.TestCase):
    def test_save_boundary_is_explicit_precached_and_under_normal_limits(self):
        app = (ROOT / "apps/pdf/app.js").read_text(encoding="utf-8")
        controller_path = ROOT / "apps/pdf/io/save-controller.js"
        controller = controller_path.read_text(encoding="utf-8")
        html = (ROOT / "apps/pdf/index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))

        self.assertTrue(controller_path.is_file())
        self.assertLessEqual(len(controller.splitlines()), 500)
        self.assertTrue(all(len(line) <= 240 for line in controller.splitlines()))
        self.assertLessEqual(len(app.splitlines()), 500)
        self.assertTrue(all(len(line) <= 240 for line in app.splitlines()))

        self.assertIn("window.InkDeskPdfSaveController.createSaveController", app)
        self.assertIn("saveController.setAvailable(true)", app)
        self.assertIn("saveController.setAvailable(false)", app)
        for moved in (
            "async function saveModifiedPdf()",
            "function download(bytes, name, type)",
            "state.doc.saveDocument()",
            "exporter.exportDocument",
            "maxPagePixels: 8000000",
            "jpegQuality: 0.91",
            "E.saveModifiedPdfBtn.onclick = saveModifiedPdf",
        ):
            self.assertNotIn(moved, app)

        for marker in (
            "async function saveModifiedPdf()",
            "state.doc.saveDocument()",
            "global.InkDeskPdfFlattenExport",
            "exporter.exportDocument",
            "maxPagePixels: 8000000",
            "jpegQuality: 0.91",
            "E.saveModifiedPdfBtn.onclick = saveModifiedPdf",
        ):
            self.assertIn(marker, controller)

        self.assertIn("io/save-controller.js?v=0.20.2.23", html)
        self.assertLess(
            html.index("flatten-export.js?v=0.20.2.23"),
            html.index("io/save-controller.js?v=0.20.2.23"),
        )
        self.assertLess(
            html.index("io/save-controller.js?v=0.20.2.23"),
            html.index("app.js?v=0.20.2.23"),
        )
        self.assertIn("'./apps/pdf/io/save-controller.js'", worker)
        self.assertNotIn("apps/pdf/app.js", policy["grandfatheredDebt"])
        self.assertNotIn("apps/pdf/io/save-controller.js", policy["grandfatheredDebt"])


if __name__ == "__main__":
    unittest.main()
