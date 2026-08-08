from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkspaceContractConsolidationTests(unittest.TestCase):
    def test_panel_controller_owns_shared_workspace_contract_helpers(self):
        controller = (ROOT / "shared/ui/workspace-panel-controller.js").read_text(encoding="utf-8")
        for marker in (
            "function moduleId(",
            "function resolvedPreference(",
            "function notifyLayoutReady(",
            "inkdesk:workspace-layout-ready",
            "moduleId,",
            "notifyLayoutReady,",
        ):
            self.assertIn(marker, controller)

    def test_workspace_layout_delegates_contract_helpers(self):
        layout = (ROOT / "shared/ui/workspace-layout.js").read_text(encoding="utf-8")
        self.assertIn("panelController.moduleId(doc)", layout)
        self.assertIn("panelController.notifyLayoutReady(doc, currentModule)", layout)
        self.assertIn("controller.resolvedPreference(key, defaultValue)", layout)
        self.assertNotIn("function safeSessionGet(", layout)
        self.assertNotIn("function moduleId(documentObject)", layout)
        self.assertNotIn("inkdesk:workspace-layout-ready", layout)

    def test_workspace_layout_leaves_grandfathered_debt(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        layout = ROOT / "shared/ui/workspace-layout.js"
        controller = ROOT / "shared/ui/workspace-panel-controller.js"
        self.assertEqual(policy["release"], "0.20.2.21")
        self.assertLessEqual(len(layout.read_text(encoding="utf-8").splitlines()), 500)
        self.assertLessEqual(len(controller.read_text(encoding="utf-8").splitlines()), 500)
        self.assertNotIn("shared/ui/workspace-layout.js", policy["grandfatheredDebt"])

    def test_node_contract_delegation_preserves_values_and_event(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
globalThis.sessionStorage = { getItem() { return null; }, setItem() {} };
globalThis.CustomEvent = function(name, init) { this.type=name; this.detail=init.detail; };
require('./shared/ui/workspace-panel-controller.js');
require('./shared/ui/workspace-layout.js');
const panel = globalThis.InkDeskWorkspacePanelController;
const layout = globalThis.InkDeskWorkspaceLayout;
if (!panel || panel.version !== '0.20.2.21') process.exit(10);
if (!layout || layout.version !== '0.20.0') process.exit(11);
const classes = { contains(name) { return name === 'office-documents'; } };
let event = null;
const doc = { body: { dataset: {}, classList: classes }, dispatchEvent(value) { event=value; } };
if (panel.moduleId(doc) !== 'documents' || layout.moduleId(doc) !== 'documents') process.exit(12);
if (layout.resolvedPreference('documents.sidebar', false) !== false) process.exit(13);
panel.notifyLayoutReady(doc, 'documents');
if (!event || event.type !== 'inkdesk:workspace-layout-ready') process.exit(14);
if (!event.detail || event.detail.version !== '0.20.0' || event.detail.moduleId !== 'documents') process.exit(15);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
