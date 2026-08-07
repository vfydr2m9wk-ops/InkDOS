from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HomeSessionRefinementTests(unittest.TestCase):
    def test_home_order_and_quiet_copy(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        positions = [
            html.index('class="hub-topbar"'),
            html.index('class="hub-intro"'),
            html.index('class="workspace-grid"'),
            html.index('class="open-any-panel"'),
            html.index('class="hub-footer"'),
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("The selected file stays on this device.", html)
        self.assertIn("v0.20.2.2 beta", html)
        self.assertNotIn("Choose a DOCX, XLS, XLSX, PPTX or PDF file.", html)

    def test_shared_shell_contains_non_invasive_title_adapter(self):
        shell = (
            ROOT / "shared/office-shell.js"
        ).read_text(encoding="utf-8")

        for marker in (
            "Document-session title adapter — 0.20.0",
            "initializeDocumentSessionAdapter",
            "office-documents",
            "office-spreadsheets",
            "office-presentations",
            "office-pdf",
            "office-txt",
            "office-epub",
            "rewriteDownloadName",
            "requestDownload.__inkdeskDocumentSessionWrapped",
            "loadFileLifecycle()",
        ):
            self.assertIn(marker, shell)

    def test_title_adapter_does_not_require_application_replacements(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        contract = manifest["documentSessionSystem"]
        self.assertFalse(
            contract["replacesCompleteApplicationFiles"]
        )
        self.assertTrue(contract["downloadNameRewriting"])
        self.assertTrue(
            contract["preservesInstalledApplicationRuntime"]
        )

    def test_shared_lifecycle_installs_unload_guard(self):
        lifecycle = (
            ROOT / "shared/file-lifecycle.js"
        ).read_text(encoding="utf-8")

        for marker in (
            "const activeControllers=new Set()",
            "function anyWorkspaceNeedsWarning()",
            "global.addEventListener('beforeunload'",
            "confirmDiscard(",
            "version:'0.20.0'",
        ):
            self.assertIn(marker, lifecycle)

    def test_visual_foundation_contains_requested_states(self):
        visual = (
            ROOT / "shared/ui/visual-foundation.css"
        ).read_text(encoding="utf-8")

        for marker in (
            ".welcome-actions .new-primary",
            ".welcome-actions .open-document-primary",
            "body.office-spreadsheets #emptyState .start-actions",
            "grid-template-columns:repeat(2,minmax(0,1fr))",
            ".file-title-editable",
        ):
            self.assertIn(marker, visual)

    def test_cache_advances_without_public_version_change(self):
        worker = (
            ROOT / "service-worker.js"
        ).read_text(encoding="utf-8")
        package = json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        )

        self.assertRegex(worker, r"const CACHE_NAME=['\"]inkdesk-shell-v[^'\"]+['\"];")
        self.assertEqual(package["version"], json.loads((ROOT / "VERSION.json").read_text())["version"])


if __name__ == "__main__":
    unittest.main()
