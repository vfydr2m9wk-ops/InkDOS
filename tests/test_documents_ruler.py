from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentsRulerTests(unittest.TestCase):
    def test_shared_runtime_contains_page_linked_controller(self):
        layout = (
            ROOT / "shared" / "ui" / "workspace-layout.js"
        ).read_text(encoding="utf-8")
        model = (
            ROOT / "shared" / "ui" / "document-ruler-model.js"
        ).read_text(encoding="utf-8")

        for marker in (
            "installDocumentsRuler",
            "dataset.inkdosRuler",
            "page-linked",
            "selectionchange",
            "contentStartDisplay",
            "contentEndDisplay",
            "InkDOSDocumentRulerModel",
        ):
            self.assertIn(marker, layout)

        for marker in (
            "visibleDocumentPage",
            "rulerMetrics",
            "rulerTickModel",
            "pointerToDocumentIndent",
            "applyDocumentIndent",
            "documentIndentState",
            "clampIndentState",
        ):
            self.assertIn(marker, model)

    def test_legacy_number_stream_is_disabled(self):
        styles = (
            ROOT / "shared" / "ui" / "workspace-layout.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "body.office-documents .ruler-track::after",
            styles,
        )
        self.assertIn("content: none !important", styles)
        self.assertIn(".inkdos-ruler-number", styles)
        self.assertIn("overflow: hidden !important", styles)

    def test_manifest_exposes_ruler_contract(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(
                encoding="utf-8"
            )
        )

        layout = manifest["uiSystem"]["workspaceLayout"]
        ruler = layout["documentsRuler"]

        self.assertEqual(layout["version"], "0.20.0")
        self.assertEqual(ruler["version"], "0.20.0")
        self.assertEqual(ruler["mode"], "active-page")
        self.assertTrue(ruler["tracksZoom"])
        self.assertTrue(ruler["tracksHorizontalScroll"])
        self.assertTrue(ruler["tracksSectionPageWidth"])
        self.assertTrue(ruler["marginZones"])

        capabilities = set(
            manifest["capabilities"]["documents"]
        )
        self.assertIn("docx-active-page-ruler", capabilities)
        self.assertIn("docx-page-width-linked-ruler", capabilities)
        self.assertIn("docx-zoom-aware-ruler", capabilities)
        self.assertIn("docx-section-aware-ruler", capabilities)

    def test_cache_and_bootstrap_advance_to_sequence_7(self):
        worker = (ROOT / "service-worker.js").read_text(
            encoding="utf-8"
        )
        bootstrap = (
            ROOT / "shared" / "office-shell.js"
        ).read_text(encoding="utf-8")

        self.assertRegex(
            worker,
            r"const CACHE_NAME=['\"]inkdos-shell-v[^'\"]+['\"];",
        )
        self.assertIn("function loadWorkspaceLayout()", bootstrap)
        self.assertIn("loadDocumentRulerModel", bootstrap)
        self.assertIn("workspace-layout.js", worker)
        self.assertIn("document-ruler-model.js", worker)
        self.assertIn("workspace-layout.css", worker)

    def test_runtime_geometry_and_indent_helpers(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
require('./shared/ui/document-ruler-model.js');
require('./shared/ui/workspace-layout.js');
const api = globalThis.InkDOSWorkspaceLayout;

if (!api || api.version !== '0.20.0') process.exit(10);

const ticks = api.rulerTickModel(816, 96);
if (!Array.isArray(ticks) || ticks.length < 60) process.exit(11);
if (ticks[0].label !== '0') process.exit(12);
if (!ticks.some(tick => tick.label === '8')) process.exit(13);
if (ticks.some(tick => tick.ratio < 0 || tick.ratio > 1)) process.exit(14);

const page = {
  offsetWidth: 816,
  __computedStyle: {
    width: '816px',
    paddingLeft: '86px',
    paddingRight: '86px'
  },
  getBoundingClientRect() {
    return {
      left: 100,
      top: 30,
      right: 508,
      bottom: 558,
      width: 408,
      height: 528
    };
  }
};

const metrics = api.rulerMetrics(page, null);
if (!metrics) process.exit(15);
if (Math.abs(metrics.zoom - 0.5) > 0.0001) process.exit(16);
if (metrics.pageWidth !== 816) process.exit(17);
if (metrics.contentWidth !== 644) process.exit(18);
if (Math.abs(metrics.contentStartDisplay - 43) > 0.001) process.exit(19);

const local = api.pointerToDocumentIndent(207.5, metrics);
if (Math.abs(local - 129) > 0.01) process.exit(20);

const clamped = api.clampIndentState(
  { left: 700, first: 720, right: 80 },
  metrics
);
if (clamped.left < 0 || clamped.first < 0 || clamped.right < 0) {
  process.exit(21);
}
if (Math.max(clamped.left, clamped.first) + clamped.right > 640.1) {
  process.exit(22);
}

let inputEvents = 0;
const block = { style: {} };
const pagesHost = {
  dispatchEvent() { inputEvents += 1; }
};

api.applyDocumentIndent(
  block,
  { left: 24, first: 36, right: 18 },
  pagesHost
);

if (block.style.marginLeft !== '24px') process.exit(23);
if (block.style.textIndent !== '12px') process.exit(24);
if (block.style.marginRight !== '18px') process.exit(25);
if (inputEvents !== 1) process.exit(26);
"""

        result = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stdout + result.stderr,
        )

    def test_package_script_is_registered(self):
        package = json.loads(
            (ROOT / "package.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            package["scripts"]["test:documents-ruler"],
            "python3 -m unittest tests.test_documents_ruler",
        )


if __name__ == "__main__":
    unittest.main()
