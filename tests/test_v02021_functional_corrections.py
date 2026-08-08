from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.20.3.1"


class FunctionalCorrectionsV02021Tests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_release_identity_is_synchronized(self):
        version = json.loads(self.read("VERSION.json"))
        package = json.loads(self.read("package.json"))
        app_manifest = json.loads(self.read("app-manifest.json"))
        release = json.loads(self.read("RELEASE_MANIFEST.json"))
        web = json.loads(self.read("manifest.webmanifest"))
        self.assertEqual(version["version"], VERSION)
        self.assertEqual(package["version"], VERSION)
        self.assertEqual(app_manifest["version"], VERSION)
        self.assertEqual(release["version"], VERSION)
        self.assertEqual(web["name"], f"InkDesk {VERSION}")
        self.assertIn(f"inkdesk-shell-v{VERSION}", self.read("service-worker.js"))

    def test_home_copy_is_the_requested_compact_form(self):
        html = self.read("index.html")
        self.assertNotIn("Consolidated modular preview", html)
        self.assertNotIn("Open, review and make focused edits", html)
        self.assertNotIn("Beta stabilization · saving creates a new local copy", html)
        self.assertGreaterEqual(html.count(f"v{VERSION} beta"), 2)
        self.assertIn("The selected file stays on this device.", html)

    def test_spreadsheet_title_is_editable_and_updates_filename_state(self):
        html = self.read("apps/spreadsheets/index.html")
        js = self.read("apps/spreadsheets/app.js")
        css = self.read("apps/spreadsheets/styles.css")
        self.assertRegex(html, r'<input id="docTitle"[^>]+aria-label="Workbook name"')
        self.assertIn("function commitWorkbookRename()", js)
        self.assertIn("book.fileName=name", js)
        self.assertIn("e.target===E.title", js)
        self.assertIn("E.title.addEventListener('blur',commitWorkbookRename)", js)
        self.assertIn("editable workbook title", css)

    def test_presentation_title_is_editable_and_updates_export_name_state(self):
        html = self.read("apps/presentations/index.html")
        js = self.read("apps/presentations/app.js")
        css = self.read("apps/presentations/styles.css")
        self.assertRegex(html, r'<input id="docTitle"[^>]+aria-label="Presentation name"')
        self.assertIn("function commitPresentationRename()", js)
        self.assertIn("pres.name=name", js)
        self.assertIn("ui.title.addEventListener('blur',commitPresentationRename)", js)
        self.assertIn("presentation-title-input", css)

    def test_pdf_obsolete_forms_badge_is_removed_without_removing_forms_capability(self):
        html = self.read("apps/pdf/index.html")
        app_manifest = json.loads(self.read("app-manifest.json"))
        self.assertNotIn("Forms: PDF.js", html)
        self.assertNotIn('id="formNote"', html)
        self.assertIn("pdf-native-acroform-interaction", app_manifest["capabilities"]["pdf"])

    def test_txt_and_epub_primary_titlebars_use_44px_reference(self):
        txt = self.read("apps/txt/styles.css")
        epub = self.read("apps/epub/styles.css")
        self.assertRegex(txt, re.compile(r"\.txt-titlebar\s*\{[^}]*height:44px;[^}]*min-height:44px;", re.S))
        self.assertRegex(epub, re.compile(r"\.epub-titlebar\{[^}]*height:44px;[^}]*min-height:44px;", re.S))
        self.assertIn("grid-template-columns:auto minmax(72px,1fr) auto", txt)
        self.assertIn("grid-template-columns:auto minmax(72px,1fr) auto", epub)

    def test_update_package_policy_remains_workflow_free(self):
        updater = self.read("scripts/apply_update_package.py")
        self.assertIn("Stable update packages cannot create, modify, or delete GitHub", updater)


if __name__ == "__main__":
    unittest.main()
