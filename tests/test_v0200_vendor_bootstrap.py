from __future__ import annotations

from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class V0200VendorBootstrapTests(unittest.TestCase):
    def test_pdf_vendor_lock_is_explicit(self):
        data = json.loads(
            (ROOT / "VENDOR_SOURCES.json").read_text(encoding="utf-8")
        )
        pdf = data["vendors"][0]
        self.assertEqual(pdf["name"], "pdfjs-dist")
        self.assertEqual(pdf["version"], "3.11.174")
        self.assertFalse(pdf["runtimeNetworkRequired"])

    def test_pdf_eval_is_disabled(self):
        script = (ROOT / "apps/pdf/app.js").read_text(encoding="utf-8")
        self.assertIn("isEvalSupported: false", script)

    def test_publication_workflow_vendors_before_validation(self):
        workflow = (
            ROOT / ".github/workflows/publish-inkdesk-v0.20.0.yml"
        ).read_text(encoding="utf-8")
        dependencies = workflow.index(
            "Install Python validation dependencies"
        )
        vendor = workflow.index("Vendor pinned PDF.js runtime")
        validate = workflow.index("Validate staged source")
        self.assertLess(dependencies, vendor)
        self.assertLess(vendor, validate)
        self.assertIn(
            "-r .release-stage/requirements-ci.txt",
            workflow,
        )
        self.assertIn("npm pack pdfjs-dist@3.11.174", workflow)
        self.assertIn("python3 scripts/generate_checksums.py", workflow)

    def test_ci_requirements_cover_unconditional_test_imports(self):
        requirements = (
            ROOT / "requirements-ci.txt"
        ).read_text(encoding="utf-8")
        for dependency in (
            "beautifulsoup4==",
            "openpyxl==",
            "Pillow==",
            "playwright==",
            "pypdf==",
        ):
            self.assertIn(dependency, requirements)


if __name__ == "__main__":
    unittest.main()
