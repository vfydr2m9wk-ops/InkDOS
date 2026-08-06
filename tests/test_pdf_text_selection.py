from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PdfTextSelectionTests(unittest.TestCase):
    def test_required_files_exist(self):
        for relative in (
            "apps/pdf/text-selection-review.js",
            "apps/pdf/app.js",
            "apps/pdf/index.html",
            "docs/PDF_TEXT_SELECTION.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_index_loads_helper_before_application(self):
        html = (ROOT / "apps" / "pdf" / "index.html").read_text(
            encoding="utf-8"
        )
        helper = html.index("text-selection-review.js?v=")
        application = html.index("app.js?v=")
        self.assertLess(helper, application)
        self.assertIn("Highlight selected text", html)
        self.assertIn("Underline selected text", html)
        self.assertIn("Comment on selected text", html)
        self.assertIn("Free marker area", html)

    def test_application_separates_text_and_free_tools(self):
        script = (ROOT / "apps" / "pdf" / "app.js").read_text(
            encoding="utf-8"
        )

        for expected in (
            "TEXT_SELECTION_TOOLS",
            "FREE_ANNOTATION_TOOLS",
            "applyTextSelection",
            "captureCurrentTextSelection",
            "annotation-group",
            "annotation.source === 'text-selection'",
        ):
            self.assertIn(expected, script)

        helper = (
            ROOT / "apps" / "pdf" / "text-selection-review.js"
        ).read_text(encoding="utf-8")
        self.assertIn("source: 'text-selection'", helper)

        free_start = script.index("const FREE_ANNOTATION_TOOLS")
        free_end = script.index("const state", free_start)
        free_block = script[free_start:free_end]

        self.assertIn("'marker'", free_block)
        self.assertIn("'text'", free_block)
        self.assertNotIn("'highlight'", free_block)
        self.assertNotIn("'underline'", free_block)
        self.assertNotIn("'comment'", free_block)

        shared = (
            ROOT / "shared" / "ui" / "workspace-layout.js"
        ).read_text(encoding="utf-8")
        self.assertIn("stopImmediatePropagation", shared)

    def test_service_worker_caches_selection_helper(self):
        worker = (ROOT / "service-worker.js").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "'./apps/pdf/text-selection-review.js'",
            worker,
        )
        self.assertRegex(
            worker,
            r"const CACHE_NAME=['\"]inkdesk-shell-v[^'\"]+['\"];",
        )

    def test_manifest_exposes_selected_text_capabilities(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        review = manifest["pdfReviewSystem"]
        self.assertEqual(review["version"], "0.20.0")
        self.assertEqual(
            review["selectedTextTools"],
            ["highlight", "underline", "comment"],
        )
        self.assertEqual(
            review["freeAnnotationTools"],
            ["marker", "text"],
        )

        capabilities = set(manifest["capabilities"]["pdf"])
        self.assertIn("pdf-selected-text-highlight", capabilities)
        self.assertIn("pdf-selected-text-underline", capabilities)
        self.assertIn("pdf-selected-text-comment", capabilities)
        self.assertIn("pdf-multiline-selection-segments", capabilities)
        self.assertIn("pdf-multipage-linked-selection", capabilities)

    def test_selection_styles_do_not_block_text_layer(self):
        styles = (
            ROOT / "shared" / "ui" / "workspace-layout.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'body.office-pdf[data-pdf-review-mode="text-selection"] '
            ".page-review-layer",
            styles,
        )
        self.assertIn("pointer-events: none !important", styles)
        self.assertIn(
            ".review-annotation.highlight.text-selection-segment",
            styles,
        )
        self.assertIn(
            ".review-annotation.underline.text-selection-segment",
            styles,
        )
        self.assertIn(
            ".review-annotation.comment.text-selection-segment",
            styles,
        )

    def test_geometry_and_annotation_builder(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
require('./apps/pdf/text-selection-review.js');
const api = globalThis.InkDeskPdfTextSelection;

if (!api || api.version !== '0.20.0') process.exit(10);

const merged = api.mergeRects([
  { x: 10, y: 20, width: 30, height: 12 },
  { x: 41, y: 20.4, width: 29, height: 11.8 },
  { x: 10, y: 40, width: 25, height: 12 }
]);

if (merged.length !== 2) process.exit(11);
if (Math.abs(merged[0].x - 10) > 0.01) process.exit(12);
if (merged[0].width < 59) process.exit(13);

const capture = {
  text: 'Selected passage',
  pages: [
    {
      page: 2,
      rects: [
        { x: 0.1, y: 0.2, w: 0.3, h: 0.04 },
        { x: 0.1, y: 0.25, w: 0.4, h: 0.04 }
      ]
    },
    {
      page: 3,
      rects: [
        { x: 0.1, y: 0.1, w: 0.2, h: 0.04 }
      ]
    }
  ]
};

let index = 0;
const annotations = api.buildAnnotations(
  capture,
  'comment',
  {
    groupId: 'group-1',
    comment: 'Review this',
    makeId: () => 'id-' + (++index)
  }
);

if (annotations.length !== 2) process.exit(14);
if (annotations[0].groupId !== 'group-1') process.exit(15);
if (annotations[1].groupId !== 'group-1') process.exit(16);
if (annotations[0].rects.length !== 2) process.exit(17);
if (annotations[0].selectedText !== 'Selected passage') process.exit(18);
if (annotations[0].comment !== 'Review this') process.exit(19);
if (annotations[0].source !== 'text-selection') process.exit(20);
if (annotations[0].pageSegmentCount !== 2) process.exit(21);
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

    def test_legacy_rectangles_remain_supported(self):
        script = (ROOT / "apps" / "pdf" / "app.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("function annotationRects", script)
        self.assertIn("Array.isArray(annotation.rects)", script)
        self.assertIn("Number(annotation.x)", script)

    def test_permanent_pdf_architecture_markers_remain_exact(self):
        script = (ROOT / "apps" / "pdf" / "app.js").read_text(
            encoding="utf-8"
        )
        for marker in (
            "pdfjsLib.GlobalWorkerOptions.workerSrc = "
            "'../../shared/vendor/pdfjs/pdf.worker.min.js'",
            "pdfjsLib.getDocument(",
            "pdfjsLib.renderTextLayer(",
            "new pdfjsLib.AnnotationLayer(",
            "state.doc.saveDocument()",
            "CACHE_RADIUS=2",
            "MAX_CANVAS_PIXELS=",
            "record.canvas.width=0",
            "schema:'inkdesk-pdf-review/2'",
            "record.page?.cleanup?.()",
            "canvas.width=0",
        ):
            self.assertIn(marker, script)


if __name__ == "__main__":
    unittest.main()
