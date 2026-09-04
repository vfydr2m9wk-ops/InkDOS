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
            html.index('class="hub-footer"'),
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('data-suite-action="open"', html)
        self.assertIn('data-suite-action="create"', html)
        self.assertIn('id="suiteSidebar"', html)
        self.assertIn('class="release-badge"', html)
        self.assertIn('aria-current="page"', html)
        self.assertIn('EPUB Reader', html)
        self.assertIn('Plain Text', html)
        self.assertIn("InkDOS", html)
        self.assertIn("Ink Desk Offline Suite", html)
        self.assertIn("Local. Offline. Private.", html)

    def test_document_session_controller_contains_non_invasive_title_adapter(self):
        controller = (
            ROOT / "shared/ui/document-session-controller.js"
        ).read_text(encoding="utf-8")
        shell = (ROOT / "shared/office-shell.js").read_text(encoding="utf-8")

        for marker in (
            "initializeDocumentSessionAdapter",
            "office-documents",
            "office-spreadsheets",
            "office-presentations",
            "office-pdf",
            "office-txt",
            "office-epub",
            "rewriteDownloadName",
            "requestDownload.__inkdosDocumentSessionWrapped",
        ):
            self.assertIn(marker, controller)

        for marker in (
            "loadFileLifecycle()",
            "loadDocumentSessionController()",
            "document-session-controller.js",
            "controller.initialize()",
        ):
            self.assertIn(marker, shell)

        self.assertNotIn("function rewriteDownloadName", shell)
        self.assertNotIn("replacementActionIds", shell)

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

    def test_home_drawer_has_accessible_close_contract(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        shell = (ROOT / "shared/suite-shell.js").read_text(encoding="utf-8")
        css = (ROOT / "shared/suite-shell.css").read_text(encoding="utf-8")
        self.assertIn('role="dialog" aria-modal="true"', html)
        for marker in ("suite-backdrop", "event.key==='Escape'", "previousFocus.focus()"):
            self.assertIn(marker, shell)
        self.assertIn(".suite-nav a[aria-current=\"page\"]", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_cache_advances_without_public_version_change(self):
        worker = (
            ROOT / "service-worker.js"
        ).read_text(encoding="utf-8")
        package = json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        )

        self.assertRegex(worker, r"const CACHE_NAME=['\"]inkdos-shell-v[^'\"]+['\"];")
        self.assertEqual(package["version"], json.loads((ROOT / "VERSION.json").read_text())["version"])


if __name__ == "__main__":
    unittest.main()
