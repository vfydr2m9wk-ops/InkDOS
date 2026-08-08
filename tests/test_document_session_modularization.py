from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentSessionModularizationTests(unittest.TestCase):
    def test_controller_owns_document_session_behavior(self):
        controller = (ROOT / "shared/ui/document-session-controller.js").read_text(
            encoding="utf-8"
        )
        for marker in (
            "InkDeskDocumentSessionController",
            "initializeDocumentSessionAdapter",
            "function normalizeName(",
            "function commitTitle(",
            "function rewriteDownloadName(",
            "requestDownload.__inkdeskDocumentSessionWrapped",
            "replacementActionIds",
            "You have unsaved changes. Continue and discard them?",
        ):
            self.assertIn(marker, controller)

    def test_office_shell_is_composition_only_for_document_session(self):
        shell = (ROOT / "shared/office-shell.js").read_text(encoding="utf-8")
        for marker in (
            "function loadFileLifecycle()",
            "function loadDocumentSessionController()",
            "document-session-controller.js",
            "InkDeskDocumentSessionReady = Promise.all([",
            "controller.initialize()",
        ):
            self.assertIn(marker, shell)
        for implementation_detail in (
            "function normalizeName(",
            "function rewriteDownloadName(",
            "replacementActionIds",
            "__inkdeskDocumentSessionWrapped",
        ):
            self.assertNotIn(implementation_detail, shell)

    def test_extraction_retires_office_shell_architecture_debt(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        shell = ROOT / "shared/office-shell.js"
        controller = ROOT / "shared/ui/document-session-controller.js"
        self.assertLessEqual(len(shell.read_text(encoding="utf-8").splitlines()), 500)
        self.assertLessEqual(len(controller.read_text(encoding="utf-8").splitlines()), 500)
        self.assertNotIn("shared/office-shell.js", policy["grandfatheredDebt"])
        self.assertEqual(policy["release"], "0.20.2.20")

    def test_controller_is_declared_and_precached(self):
        manifest = json.loads((ROOT / "app-manifest.json").read_text(encoding="utf-8"))
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        contract = manifest["documentSessionSystem"]
        self.assertEqual(contract["version"], "0.20.0")
        self.assertEqual(contract["runtime"], "shared/ui/document-session-controller.js")
        self.assertEqual(contract["architectureRelease"], "0.20.2.14")
        self.assertIn("'./shared/ui/document-session-controller.js'", worker)


if __name__ == "__main__":
    unittest.main()
