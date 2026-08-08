from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UNIFIED = ROOT / "shared" / "ui" / "workspace-unification-v02031.css"
FOUNDATION = ROOT / "shared" / "ui" / "visual-foundation-v0203.css"


class UICorrection02031Tests(unittest.TestCase):
    def test_spreadsheet_footer_and_add_sheet_contract(self):
        css = UNIFIED.read_text(encoding="utf-8")
        app = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        tabs = (ROOT / "apps/spreadsheets/worksheet-tabs.js").read_text(encoding="utf-8")
        engine = (ROOT / "apps/spreadsheets/xlsx-engine.js").read_text(encoding="utf-8")
        package = (ROOT / "apps/spreadsheets/worksheet-package.js").read_text(encoding="utf-8")
        self.assertIn("#sheetTabs > #addSheetBtn", css)
        self.assertIn("InkDeskSpreadsheetWorksheetTabs.render", app)
        self.assertIn("add.id = 'addSheetBtn'", tabs)
        self.assertIn("InkDeskSpreadsheetWorksheetPackage.appendNewSheets", engine)
        self.assertIn("async function appendNewSheets", package)
        self.assertIn("Workbook package metadata is incomplete", package)
        self.assertIn("activeTab", package)

    def test_pdf_tabs_are_allocated_full_navigation_width(self):
        css = UNIFIED.read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:238px minmax(0,1fr)!important", css)
        self.assertIn("body.office-pdf .sidebar-tabs", css)
        self.assertIn("grid-template-columns:max-content max-content max-content max-content!important", css)
        self.assertIn("justify-content:space-between!important", css)
        self.assertIn("font-size:10px!important", css)

    def test_presentations_has_only_bottom_visible_zoom(self):
        css = UNIFIED.read_text(encoding="utf-8")
        self.assertIn("body.office-presentations #toolsView #zoomRange", css)
        self.assertIn("display:none!important", css)
        self.assertIn("body.office-presentations .present-top-action svg", css)
        self.assertIn("fill:none!important", css)

    def test_launcher_registry_order_is_visually_normalized(self):
        css = FOUNDATION.read_text(encoding="utf-8")
        self.assertIn("Launcher alignment correction", css)
        self.assertIn(".workspace-card > .app-icon{grid-column:1!important", css)
        self.assertIn(".workspace-card > .workspace-copy{grid-column:2!important", css)
        self.assertIn(".workspace-card > .open-arrow{grid-column:3!important", css)
        self.assertIn("grid-template-columns:42px minmax(0,1fr) 18px!important", css)

    def test_documents_txt_epub_are_not_structurally_reworked(self):
        css = UNIFIED.read_text(encoding="utf-8")
        correction = css.split("UI correction pass 6", 1)[1]
        self.assertNotIn("body.office-documents", correction)
        self.assertNotIn("body.office-txt", correction)
        self.assertNotIn("body.office-epub", correction)


if __name__ == "__main__":
    unittest.main()
