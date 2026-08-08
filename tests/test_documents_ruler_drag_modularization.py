from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentsRulerDragModularizationTests(unittest.TestCase):
    def test_drag_controller_owns_pointer_lifecycle(self):
        controller = (ROOT / "shared/ui/document-ruler-drag-controller.js").read_text(
            encoding="utf-8"
        )
        for marker in (
            "InkDeskDocumentRulerDragController",
            "function startDrag(",
            "function moveDrag(",
            "function endDrag(",
            "'pointerdown'",
            "'pointermove'",
            "'pointerup'",
            "'pointercancel'",
            "setPointerCapture",
            "model.applyDocumentIndent(",
        ):
            self.assertIn(marker, controller)

    def test_workspace_layout_delegates_drag_but_keeps_dom_sync(self):
        layout = (ROOT / "shared/ui/workspace-layout.js").read_text(encoding="utf-8")
        self.assertIn("InkDeskDocumentRulerDragController", layout)
        self.assertIn("dragControllerFactory.create({", layout)
        self.assertIn("function renderTicks(", layout)
        self.assertIn("function updateHandles(", layout)
        self.assertIn("function sync(", layout)
        self.assertIn("MutationObserver", layout)
        self.assertIn("ResizeObserver", layout)
        for implementation in (
            "function startDrag(",
            "function moveDrag(",
            "function endDrag(",
            "setPointerCapture",
        ):
            self.assertNotIn(implementation, layout)

    def test_drag_controller_load_order_and_offline_precache(self):
        shell = (ROOT / "shared/office-shell.js").read_text(encoding="utf-8")
        documents = (ROOT / "apps/documents/index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")

        self.assertIn("function loadDocumentRulerDragController()", shell)
        self.assertIn("document-ruler-drag-controller.js", shell)
        self.assertLess(
            shell.index("loadDocumentRulerDragController();"),
            shell.index("loadWorkspaceLayoutRuntime();"),
        )

        model_tag = "document-ruler-model.js?v=0.20.2.26"
        drag_tag = "document-ruler-drag-controller.js?v=0.20.2.26"
        layout_tag = "workspace-layout.js?v=0.20.2.26"
        self.assertIn(model_tag, documents)
        self.assertIn(drag_tag, documents)
        self.assertIn(layout_tag, documents)
        self.assertLess(documents.index(model_tag), documents.index(drag_tag))
        self.assertLess(documents.index(drag_tag), documents.index(layout_tag))
        self.assertIn("'./shared/ui/document-ruler-drag-controller.js'", worker)

    def test_architecture_ratchet_is_lowered(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        layout = ROOT / "shared/ui/workspace-layout.js"
        controller = ROOT / "shared/ui/document-ruler-drag-controller.js"
        shell = ROOT / "shared/office-shell.js"
        layout_lines = len(layout.read_text(encoding="utf-8").splitlines())
        controller_lines = len(controller.read_text(encoding="utf-8").splitlines())
        shell_lines = len(shell.read_text(encoding="utf-8").splitlines())

        self.assertEqual(policy["release"], "0.20.2.26")
        self.assertLessEqual(layout_lines, 500)
        self.assertLessEqual(controller_lines, 500)
        self.assertLessEqual(shell_lines, 500)
        self.assertNotIn("shared/ui/workspace-layout.js", policy["grandfatheredDebt"])

    def test_node_drag_lifecycle_preserves_indent_application(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
const globalListeners = {};
globalThis.addEventListener = (name, fn) => { globalListeners[name] = fn; };
globalThis.removeEventListener = (name, fn) => {
  if (globalListeners[name] === fn) delete globalListeners[name];
};
require('./shared/ui/document-ruler-drag-controller.js');
const factory = globalThis.InkDeskDocumentRulerDragController;
if (!factory || factory.version !== '0.20.2.26') process.exit(10);

const rulerListeners = {};
const ruler = {
  addEventListener(name, fn) { rulerListeners[name] = fn; },
  removeEventListener(name, fn) {
    if (rulerListeners[name] === fn) delete rulerListeners[name];
  }
};
const target = {
  id: 'leftIndent',
  closest(selector) { return selector === '.ruler-handle' ? this : null; },
  setPointerCapture() { this.captured = true; }
};
const track = { contains(value) { return value === target; } };
const block = { style: {} };
const pagesHost = {};
let metrics = { zoom: 1, contentWidth: 500 };
let scheduled = 0;
let applied = null;
let handles = null;
let status = '';
const documentObject = {
  getElementById(id) {
    if (id === 'statusText') return { set textContent(value) { status = value; } };
    return null;
  }
};
const model = {
  rulerMetrics() { return metrics; },
  pointerToDocumentIndent(clientX) { return clientX; },
  clampIndentState(state) { return state; },
  applyDocumentIndent(targetBlock, state, host) {
    if (targetBlock !== block || host !== pagesHost) process.exit(11);
    applied = {...state};
  }
};
const controller = factory.create({
  documentObject,
  ruler,
  track,
  pagesHost,
  model,
  scheduleSync() { scheduled += 1; },
  sync() {},
  currentBlockState() {
    return {block, state: {left: 10, first: 20, right: 5}};
  },
  updateHandles(state) { handles = {...state}; },
  getMetrics() { return metrics; },
  setMetrics(value) { metrics = value; },
  getActivePage() { return {}; }
});
if (!controller || controller.version !== '0.20.2.26') process.exit(12);

const down = {
  target,
  pointerId: 7,
  clientX: 100,
  preventDefault() {},
  stopImmediatePropagation() {}
};
rulerListeners.pointerdown(down);
if (!target.captured || !controller.active()) process.exit(13);

globalListeners.pointermove({
  pointerId: 7,
  clientX: 120,
  preventDefault() {},
  stopImmediatePropagation() {}
});
if (!applied || applied.left !== 30 || applied.first !== 40 || applied.right !== 5) {
  process.exit(14);
}
if (!handles || handles.left !== 30 || status !== 'Paragraph indentation updated') {
  process.exit(15);
}

globalListeners.pointerup({
  pointerId: 7,
  preventDefault() {},
  stopImmediatePropagation() {}
});
if (controller.active() || scheduled < 2) process.exit(16);
controller.destroy();
if (rulerListeners.pointerdown || globalListeners.pointermove || globalListeners.pointerup) {
  process.exit(17);
}
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
