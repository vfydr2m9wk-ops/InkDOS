from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UnifiedOpenRouterTests(unittest.TestCase):
    def test_hub_and_workspaces_expose_unified_navigation(self):
        hub = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="openAnyDocument"', hub)
        self.assertIn('id="openAnyInput"', hub)
        self.assertIn('shared/file-router.js', hub)
        self.assertIn('shared/hub-open.js', hub)

        router = (ROOT / "shared/file-router.js").read_text(encoding="utf-8")
        for extension, workspace in (
            ("docx", "apps/documents/index.html"),
            ("xls", "apps/spreadsheets/index.html"),
            ("xlsx", "apps/spreadsheets/index.html"),
            ("pptx", "apps/presentations/index.html"),
        ):
            self.assertIn(extension, router)
            self.assertIn(workspace, router)
        self.assertIn("indexedDB", router)
        self.assertIn("inkdesk:open-file", router)
        self.assertIn("location.protocol==='file:'", router)

        for workspace in ("documents", "spreadsheets", "presentations"):
            html = (ROOT / "apps" / workspace / "index.html").read_text(encoding="utf-8")
            app = (ROOT / "apps" / workspace / "app.js").read_text(encoding="utf-8")
            self.assertIn('class="icon-btn', html)
            self.assertIn('home-link', html)
            self.assertIn('href="../../index.html"', html)
            self.assertIn('target="_top"', html)
            self.assertIn('shared/file-router.js', html)
            self.assertIn('InkDeskFileRouter.attachWorkspace', app)

        service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("./shared/file-router.js", service_worker)
        self.assertIn("./shared/hub-open.js", service_worker)


if __name__ == "__main__":
    unittest.main()
