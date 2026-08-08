from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkspacePanelModularizationTests(unittest.TestCase):
    def test_panel_controller_owns_cross_workspace_panel_behavior(self):
        controller = (ROOT / "shared/ui/workspace-panel-controller.js").read_text(
            encoding="utf-8"
        )
        for marker in (
            "InkDeskWorkspacePanelController",
            "function applyDocuments(",
            "function applyPresentations(",
            "function applyPdf(",
            "function applySpreadsheet(",
            "documents.sidebar",
            "presentations.thumbnails",
            "presentations.inspector",
            "presentations.notes",
            "pdf.sidebar",
            "sidebar-hidden",
            "hide-slides",
            "hide-inspector",
            "hide-notes",
            "sidebar-collapsed",
            "inkdeskFormulaBar",
            "inkdeskStatusLayout",
        ):
            self.assertIn(marker, controller)

    def test_workspace_layout_keeps_ruler_and_delegates_panel_state(self):
        layout = (ROOT / "shared/ui/workspace-layout.js").read_text(encoding="utf-8")
        self.assertIn("installDocumentsRuler", layout)
        self.assertIn("InkDeskWorkspacePanelController", layout)
        self.assertIn("panelController.apply(doc, currentModule)", layout)
        for implementation_detail in (
            "function applyPresentations(",
            "function applyPdf(",
            "function applySpreadsheet(",
            "safeSessionSet('presentations.thumbnails'",
            "safeSessionSet('pdf.sidebar'",
        ):
            self.assertNotIn(implementation_detail, layout)

    def test_office_shell_loads_panel_controller_before_workspace_layout(self):
        shell = (ROOT / "shared/office-shell.js").read_text(encoding="utf-8")
        self.assertIn("function loadWorkspacePanelController()", shell)
        self.assertIn("workspace-panel-controller.js", shell)
        self.assertIn("return loadWorkspacePanelController().then(function ()", shell)
        self.assertLess(
            shell.index("loadWorkspacePanelController().then"),
            shell.index("return loadWorkspaceLayoutRuntime();"),
        )

    def test_controller_is_precached_and_documents_direct_load_is_ordered(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        documents = (ROOT / "apps/documents/index.html").read_text(encoding="utf-8")
        self.assertIn("'./shared/ui/workspace-panel-controller.js'", worker)
        controller_tag = "workspace-panel-controller.js?v=0.20.2.29"
        layout_tag = "workspace-layout.js?v=0.20.2.29"
        self.assertIn(controller_tag, documents)
        self.assertIn(layout_tag, documents)
        self.assertLess(documents.index(controller_tag), documents.index(layout_tag))

    def test_architecture_ratchet_shrinks_workspace_layout_debt(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        layout = ROOT / "shared/ui/workspace-layout.js"
        controller = ROOT / "shared/ui/workspace-panel-controller.js"
        self.assertEqual(policy["release"], "0.20.2.29")
        self.assertLessEqual(len(controller.read_text(encoding="utf-8").splitlines()), 500)
        self.assertLessEqual(len(layout.read_text(encoding="utf-8").splitlines()), 500)
        self.assertNotIn("shared/ui/workspace-layout.js", policy["grandfatheredDebt"])


if __name__ == "__main__":
    unittest.main()
