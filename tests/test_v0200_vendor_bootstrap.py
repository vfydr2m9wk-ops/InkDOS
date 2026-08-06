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
        self.assertEqual(
            pdf["publicationStep"],
            "scripts/run_release_validation.py",
        )

    def test_pdf_eval_is_disabled(self):
        script = (ROOT / "apps/pdf/app.js").read_text(encoding="utf-8")
        self.assertIn("isEvalSupported: false", script)

    def test_release_gate_validates_vendor_and_checksums(self):
        script = (
            ROOT / "scripts/run_release_validation.py"
        ).read_text(encoding="utf-8")
        for marker in (
            "Repository validation",
            "Source audit",
            "Unit and package tests",
            "Browser regressions",
            "Checksum verification",
        ):
            self.assertIn(marker, script)

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
