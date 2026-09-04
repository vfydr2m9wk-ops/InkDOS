from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentsRulerModelModularizationTests(unittest.TestCase):
    def test_model_owns_pure_ruler_and_indent_helpers(self):
        model = (ROOT / "shared/ui/document-ruler-model.js").read_text(encoding="utf-8")
        for marker in (
            "InkDOSDocumentRulerModel",
            "function rulerTickModel(",
            "function rulerMetrics(",
            "function visibleDocumentPage(",
            "function selectedDocumentBlock(",
            "function documentIndentState(",
            "function clampIndentState(",
            "function pointerToDocumentIndent(",
            "function applyDocumentIndent(",
        ):
            self.assertIn(marker, model)

    def test_workspace_layout_keeps_dom_controller_and_delegates_math(self):
        layout = (ROOT / "shared/ui/workspace-layout.js").read_text(encoding="utf-8")
        self.assertIn("function installDocumentsRuler(", layout)
        self.assertIn("InkDOSDocumentRulerModel", layout)
        self.assertIn("model.rulerMetrics(", layout)
        drag = (ROOT / "shared/ui/document-ruler-drag-controller.js").read_text(encoding="utf-8")
        self.assertIn("model.pointerToDocumentIndent(", drag)
        self.assertIn("model.applyDocumentIndent(", drag)
        for implementation in (
            "function finiteNumber(",
            "function rulerTickModel(",
            "function rulerMetrics(",
            "function documentIndentState(",
            "function clampIndentState(",
            "function pointerToDocumentIndent(",
            "function applyDocumentIndent(",
        ):
            self.assertNotIn(implementation, layout)

    def test_model_load_order_and_offline_precache(self):
        shell = (ROOT / "shared/office-shell.js").read_text(encoding="utf-8")
        documents = (ROOT / "apps/documents/index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")

        self.assertIn("function loadDocumentRulerModel()", shell)
        self.assertIn("document-ruler-model.js", shell)
        self.assertLess(
            shell.index(".then(loadDocumentRulerModel)"),
            shell.index(".then(loadWorkspaceLayoutRuntime)"),
        )

        model_tag = "document-ruler-model.js?v=1.0.0-beta.5"
        layout_tag = "workspace-layout.js?v=1.0.0-beta.5"
        self.assertIn(model_tag, documents)
        self.assertIn(layout_tag, documents)
        self.assertLess(documents.index(model_tag), documents.index(layout_tag))
        self.assertIn("'./shared/ui/document-ruler-model.js'", worker)

    def test_architecture_ratchet_is_bounded(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        layout = ROOT / "shared/ui/workspace-layout.js"
        model = ROOT / "shared/ui/document-ruler-model.js"
        shell = ROOT / "shared/office-shell.js"
        layout_lines = len(layout.read_text(encoding="utf-8").splitlines())
        model_lines = len(model.read_text(encoding="utf-8").splitlines())
        shell_lines = len(shell.read_text(encoding="utf-8").splitlines())

        self.assertEqual(policy["release"], "1.0.0-beta.5")
        self.assertLessEqual(layout_lines, 500)
        self.assertLessEqual(model_lines, 500)
        self.assertLessEqual(shell_lines, 500)
        self.assertNotIn("shared/ui/workspace-layout.js", policy["grandfatheredDebt"])

    def test_node_model_and_compatibility_api_match(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
require('./shared/ui/document-ruler-model.js');
require('./shared/ui/workspace-layout.js');
const model = globalThis.InkDOSDocumentRulerModel;
const layout = globalThis.InkDOSWorkspaceLayout;
if (!model || model.version !== '0.20.3.0') process.exit(10);
if (!layout || layout.version !== '0.20.0') process.exit(11);
const a = model.rulerTickModel(816, 96);
const b = layout.rulerTickModel(816, 96);
if (JSON.stringify(a) !== JSON.stringify(b)) process.exit(12);
const metrics = {contentWidth: 644};
const state = {left: 700, first: 720, right: 80};
if (JSON.stringify(model.clampIndentState(state, metrics)) !==
    JSON.stringify(layout.clampIndentState(state, metrics))) process.exit(13);
"""
        result = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
