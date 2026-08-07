from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


class PdfUnifiedSaveTests(unittest.TestCase):
    def test_required_assets_exist(self):
        for relative in (
            "apps/pdf/flatten-export.js",
            "apps/pdf/flatten-export.css",
            "apps/pdf/index.html",
            "apps/pdf/app.js",
            "apps/pdf/io/save-controller.js",
            "docs/PDF_UNIFIED_SAVE.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_pdf_has_one_visible_save_command(self):
        html = (ROOT / "apps/pdf/index.html").read_text(
            encoding="utf-8"
        )

        self.assertEqual(
            html.count('id="saveModifiedPdfBtn"'),
            1,
        )
        self.assertIn(
            'aria-label="Save annotated PDF"',
            html,
        )
        self.assertIn('id="fullscreenBtn"', html)
        self.assertIn('id="systemOpenBtn"', html)

        for removed in (
            'id="exportReviewBtn"',
            'id="importReviewBtn"',
            'id="downloadBtn"',
            'id="printBtn"',
            'id="reviewImportInput"',
            "Export review",
            "Save PDF copy",
        ):
            self.assertNotIn(removed, html)

    def test_exporter_loads_before_pdf_application(self):
        html = (ROOT / "apps/pdf/index.html").read_text(
            encoding="utf-8"
        )

        exporter = html.index('src="flatten-export.js')
        save_controller = html.index('src="io/save-controller.js')
        application = html.index('src="app.js')

        self.assertLess(exporter, save_controller)
        self.assertLess(save_controller, application)
        self.assertIn(
            "flatten-export.css?v=0.20.2.13",
            html,
        )

    def test_pdf_save_controller_uses_both_save_paths(self):
        app = (ROOT / "apps/pdf/app.js").read_text(encoding="utf-8")
        controller = (ROOT / "apps/pdf/io/save-controller.js").read_text(encoding="utf-8")

        self.assertIn("window.InkDeskPdfSaveController.createSaveController", app)
        for marker in (
            "global.InkDeskPdfFlattenExport",
            "state.annotations.length > 0",
            "state.doc.saveDocument()",
            "exporter.exportDocument",
            "Annotated PDF saved",
            "E.saveModifiedPdfBtn.onclick = saveModifiedPdf",
            "maxPagePixels: 8000000",
            "jpegQuality: 0.91",
        ):
            self.assertIn(marker, controller)

        for removed in (
            "state.doc.saveDocument()",
            "exporter.exportDocument",
            "E.saveModifiedPdfBtn.onclick = saveModifiedPdf",
            "function exportReview()",
        ):
            self.assertNotIn(removed, app)

    def test_manifest_exposes_save_contract_and_visual_foundation(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(
                encoding="utf-8"
            )
        )

        contract = manifest["pdfSaveSystem"]
        self.assertEqual(contract["version"], "0.20.0")
        self.assertEqual(contract["visualFoundation"], "0.20.0")
        self.assertFalse(contract["annotatedExportTextSelectable"])
        self.assertEqual(
            contract["visibleActions"],
            [
                "open",
                "save",
                "open-in-system-viewer",
                "fullscreen",
            ],
        )
        self.assertIn(
            "saveDocument",
            contract["saveModes"]["withoutInkDeskAnnotations"],
        )
        self.assertIn(
            "flattened",
            contract["saveModes"]["withInkDeskAnnotations"],
        )

        capabilities = set(manifest["capabilities"]["pdf"])
        self.assertIn("pdf-unified-save", capabilities)
        self.assertIn(
            "pdf-flatten-review-to-copy",
            capabilities,
        )
        self.assertNotIn(
            "pdf-review-sidecar-import-export",
            capabilities,
        )
        self.assertNotIn("pdf-original-download", capabilities)

    def test_service_worker_caches_exporter(self):
        worker = (ROOT / "service-worker.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "'./apps/pdf/flatten-export.css'",
            worker,
        )
        self.assertIn(
            "'./apps/pdf/flatten-export.js'",
            worker,
        )
        self.assertRegex(worker, r"const CACHE_NAME=['\"]inkdesk-shell-v[^'\"]+['\"];")

    def test_pure_pdf_builder_and_geometry(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        with tempfile.TemporaryDirectory(
            prefix="inkdesk-pdf-builder-"
        ) as temp_name:
            output = Path(temp_name) / "flattened.pdf"

            script = r"""
const fs = require('fs');
require('./apps/pdf/flatten-export.js');
const api = globalThis.InkDeskPdfFlattenExport;

if (!api || api.version !== '0.20.0') process.exit(10);

const rectangle = api.rectToPixels(
  { x: 0.1, y: 0.2, w: 0.3, h: 0.04 },
  1000,
  1500
);

if (rectangle.x !== 100) process.exit(11);
if (rectangle.y !== 300) process.exit(12);
if (rectangle.width !== 300) process.exit(13);
if (rectangle.height !== 60) process.exit(14);

const oldRect = api.annotationRects({
  x: 0.2,
  y: 0.3,
  w: 0.4,
  h: 0.05
});

if (oldRect.length !== 1) process.exit(15);

const jpeg = new Uint8Array([0xff, 0xd8, 0xff, 0xd9]);
const bytes = api.buildPdfFromJpegPages([
  {
    jpeg,
    pixelWidth: 10,
    pixelHeight: 10,
    pageWidth: 612,
    pageHeight: 792
  },
  {
    jpeg,
    pixelWidth: 10,
    pixelHeight: 10,
    pageWidth: 792,
    pageHeight: 612
  }
]);

const text = Buffer.from(bytes).toString('latin1');
if (!text.startsWith('%PDF-1.4')) process.exit(16);
if (!text.includes('/Subtype /Image')) process.exit(17);
if (!text.includes('/Count 2')) process.exit(18);
if (!text.includes('xref')) process.exit(19);
if (!text.includes('startxref')) process.exit(20);

fs.writeFileSync(process.argv[1], Buffer.from(bytes));
"""

            result = subprocess.run(
                [node, "-e", script, str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                result.stdout + result.stderr,
            )

            reader = PdfReader(output, strict=False)
            self.assertEqual(len(reader.pages), 2)

            first = reader.pages[0].mediabox
            second = reader.pages[1].mediabox

            self.assertAlmostEqual(float(first.width), 612)
            self.assertAlmostEqual(float(first.height), 792)
            self.assertAlmostEqual(float(second.width), 792)
            self.assertAlmostEqual(float(second.height), 612)

    def test_package_script_is_registered(self):
        package = json.loads(
            (ROOT / "package.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            package["scripts"]["test:pdf-unified-save"],
            "python3 -m unittest tests.test_pdf_unified_save",
        )


if __name__ == "__main__":
    unittest.main()
