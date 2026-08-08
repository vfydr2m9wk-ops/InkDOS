from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_required_entry_points_exist(self):
        for rel in (
            "index.html",
            "apps/documents/index.html",
            "apps/spreadsheets/index.html",
            "apps/presentations/index.html",
        ):
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_manifest_entry_points_exist(self):
        manifest = json.loads((ROOT / "app-manifest.json").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / manifest["entryPoint"]).is_file())
        for launcher in manifest["launchers"]:
            self.assertTrue((ROOT / launcher["entryPoint"]).is_file(), launcher["entryPoint"])

    def test_release_versions_are_consistent(self):
        version_info = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "app-manifest.json").read_text(encoding="utf-8"))
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        release_manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))

        expected = version_info["version"]
        self.assertRegex(expected, r"^\d+\.\d+\.\d+(?:\.\d+)*(?:-[0-9A-Za-z.-]+)?$")
        self.assertEqual(manifest["version"], expected)
        self.assertEqual(package["version"], expected)
        self.assertEqual(release_manifest["version"], expected)

    def test_no_device_specific_absolute_paths(self):
        bad = re.compile("file:///var/mobile/" + "Containers|/var/mobile/" + "Containers")
        for path in ROOT.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".md", ".json", ".py"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertIsNone(bad.search(text), str(path.relative_to(ROOT)))

    def test_spreadsheet_runtime_has_no_remote_script(self):
        html = (ROOT / "apps/spreadsheets/index.html").read_text(encoding="utf-8")
        self.assertNotIn("https://cdn.sheetjs.com", html)
        self.assertNotIn("sheetjs-bridge.js", html)
        self.assertIn(".xls,.xlsx", html)
        self.assertIn("xls-biff8-engine.js", html)
        self.assertNotIn("https://cdn.sheetjs.com", html)


    def test_stable_incremental_workflow_is_present(self):
        workflow_dir = ROOT / ".github" / "workflows"
        apply_path = workflow_dir / "apply-inkdesk-update.yml"
        self.assertTrue(apply_path.is_file())
        self.assertFalse(
            (workflow_dir / "publish-inkdesk-v0.20.0.yml").exists()
        )
        workflow = apply_path.read_text(encoding="utf-8")
        for marker in (
            "InkDesk integrity and update",
            "Select and inspect update package",
            "Apply package transaction",
            "Commit and push applied update",
            "Write final Actions summary",
            "actions/checkout@v6",
            "actions/setup-python@v6",
        ):
            self.assertIn(marker, workflow)
        self.assertNotIn("--allow-workflow-changes", workflow)
        self.assertIn(
            "Update packages cannot create or modify GitHub workflow files",
            workflow,
        )

    def test_docx_parser_reads_standard_word_package_parts(self):
        parser = (ROOT / "apps/documents/docx-parser.js").read_text(encoding="utf-8")
        self.assertIn("word/document.xml", parser)
        self.assertIn("word/numbering.xml", parser)
        self.assertIn("_rels/document.xml.rels", parser)
        self.assertIn("word/numbering.xml", parser)


    def test_docx_layout_uses_webkit_safe_pagination(self):
        parser = (ROOT / "apps/documents/docx-parser.js").read_text(encoding="utf-8")
        app = (ROOT / "apps/documents/app.js").read_text(encoding="utf-8")
        css = (ROOT / "apps/documents/styles.css").read_text(encoding="utf-8")
        html = (ROOT / "apps/documents/index.html").read_text(encoding="utf-8")
        self.assertIn("pageSpec", parser)
        self.assertIn("softPageBreakBefore", parser)
        self.assertIn("mapSymbol", parser)
        self.assertIn("styles.xml", parser)
        self.assertIn("pagination-content-measure", app)
        self.assertIn("tolerance=3", app)
        self.assertIn("pagination-measure", css)
        self.assertIn("docx-parser.js?v=0.20.2.25", html)

    def test_export_writers_use_standard_ooxml_part_paths(self):
        docx = (ROOT / "apps/documents/docx-writer.js").read_text(encoding="utf-8")
        xlsx = (ROOT / "apps/spreadsheets/xlsx-engine.js").read_text(encoding="utf-8")
        pptx = (ROOT / "apps/presentations/io/file-controller.js").read_text(encoding="utf-8")
        self.assertIn("/word/document.xml", docx)
        self.assertNotIn("/documents/document.xml", docx)
        self.assertIn("xl/worksheets/", xlsx)
        self.assertNotIn("workspreadsheets", xlsx)
        self.assertIn("ppt/slides/slide", pptx)
        self.assertNotIn("ppt/presentations/slide", pptx)
        self.assertNotIn("notesPresentations", pptx)



    def test_spreadsheet_object_urls_are_released(self):
        source = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        self.assertIn("function revokeWorkbookObjectUrls(workbook)", source)
        self.assertIn("revokeWorkbookObjectUrls(book);book=nextBook", source)
        self.assertIn("revokeWorkbookObjectUrls(book);book=LocalXLSX.createBlank()", source)
        self.assertIn("window.addEventListener('pagehide',()=>revokeWorkbookObjectUrls(book),{once:true})", source)

    def test_shared_runtime_and_vendor_files_are_canonical(self):
        for html_path in (
            ROOT / "apps/documents/index.html",
            ROOT / "apps/spreadsheets/index.html",
            ROOT / "apps/presentations/index.html",
        ):
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("shared/office-runtime.js", html)
            self.assertIn("shared/vendor/jszip.min.js", html)
        self.assertEqual(list(ROOT.glob("apps/*/vendor/jszip.min.js")), [])
        self.assertEqual(list(ROOT.glob("apps/*/vendor/pako_inflate.min.js")), [])
        self.assertTrue((ROOT / "shared/vendor/jszip.min.js").is_file())
        self.assertTrue((ROOT / "shared/vendor/pako_inflate.min.js").is_file())

    def test_generated_test_artifacts_are_ignored(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("test-results/", "tests/browser/results/", "*.pyc"):
            self.assertIn(pattern, ignored)

    def test_office_package_safety_limits_are_present(self):
        runtime = (ROOT / "shared/office-runtime.js").read_text(encoding="utf-8")
        for token in ("maxCompressedBytes", "maxEntries", "maxUncompressedBytes", "maxCompressionRatio", "validateZipPackage"):
            self.assertIn(token, runtime)
        for source_path in (
            ROOT / "apps/documents/docx-parser.js",
            ROOT / "apps/spreadsheets/xlsx-engine.js",
            ROOT / "apps/presentations/io/file-controller.js",
        ):
            self.assertIn("validateZipPackage", source_path.read_text(encoding="utf-8"))

    def test_formula_zero_visibility_is_format_driven(self):
        source = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        self.assertIn("cell.style?.hideZero", source)
        self.assertNotIn("viewMode==='form'&&cell.f&&Number(effective)===0", source)


if __name__ == "__main__":
    unittest.main()
