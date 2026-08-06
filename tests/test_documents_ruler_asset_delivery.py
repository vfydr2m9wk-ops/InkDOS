from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentsRulerAssetDeliveryTests(unittest.TestCase):
    def test_documents_entry_point_requests_ruler_assets_before_shell(self):
        html = (ROOT / "apps/documents/index.html").read_text(
            encoding="utf-8"
        )
        for marker in (
            "../../shared/ui/workspace-layout.css",
            "../../shared/ui/workspace-layout.js",
            "../../shared/office-shell.js",
        ):
            self.assertIn(marker, html)
        self.assertLess(
            html.index("../../shared/ui/workspace-layout.js"),
            html.index("../../shared/office-shell.js"),
        )

    def test_shell_keeps_shared_visual_and_layout_bootstraps(self):
        shell = (ROOT / "shared/office-shell.js").read_text(
            encoding="utf-8"
        )
        for marker in (
            "addStylesheet('design-tokens.css')",
            "addStylesheet('components.css')",
            "addStylesheet('workspace-layout.css')",
            "addStylesheet('visual-foundation.css')",
            "InkDeskWorkspaceLayout",
        ):
            self.assertIn(marker, shell)

    def test_service_worker_caches_shared_ruler_assets(self):
        worker = (ROOT / "service-worker.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("inkdesk-shell-v0.20.0", worker)
        self.assertIn("'./shared/ui/workspace-layout.css'", worker)
        self.assertIn("'./shared/ui/workspace-layout.js'", worker)
        self.assertIn("const APP_SHELL_URLS=", worker)
        self.assertIn("APP_SHELL_URLS.has(key.url)", worker)

    def test_local_css_disables_retired_number_string(self):
        styles = (ROOT / "apps/documents/styles.css").read_text(
            encoding="utf-8"
        )
        self.assertIn("InkDesk 0.20.0 ruler delivery fallback", styles)
        self.assertIn("body.office-documents .ruler-track::after", styles)
        self.assertIn("content: none !important", styles)


if __name__ == "__main__":
    unittest.main()
