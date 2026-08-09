from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "shared" / "ui" / "spreadsheets-beta1-polish.css"


class SpreadsheetVisualPolishBeta1Tests(unittest.TestCase):
    def test_overlay_is_small_scoped_and_presentation_only(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 220)
        self.assertIn("body.office-spreadsheets", text)
        for forbidden in ("indexedDB", "localStorage", "fetch(", "XMLSerializer", "JSZip", "eval" + "(", "Function" + "("):
            self.assertNotIn(forbidden, text)

    def test_overlay_loads_after_existing_unification_layer(self):
        shell = (ROOT / "shared" / "office-shell.js").read_text(encoding="utf-8")
        unified = shell.index("addStylesheet('workspace-unification-v02031.css')")
        polish = shell.index("addStylesheet('spreadsheets-beta1-polish.css')")
        self.assertGreater(polish, unified)

    def test_offline_shell_precaches_overlay(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("./shared/ui/spreadsheets-beta1-polish.css", worker)

    def test_formula_bar_hierarchy_is_explicit(self):
        text = CSS.read_text(encoding="utf-8")
        for marker in ("#nameBox", ".formula-row .fx", ".formula-editor:focus-within", "#formulaInput", "#addFormulaRangeBtn"):
            self.assertIn(marker, text)
        self.assertIn("height:40px!important", text)
        self.assertIn("width:74px!important", text)

    def test_grid_selection_and_format_state_use_spreadsheet_accent(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn(".cell.selected", text)
        self.assertIn("outline:2px solid var(--ink-accent)!important", text)
        self.assertIn(".axis-active", text)
        self.assertIn("button.active-format", text)

    def test_worksheet_add_delete_controls_remain_trailing_and_visible(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("#sheetTabs > #addSheetBtn", text)
        self.assertIn("#sheetTabs > #deleteSheetBtn", text)
        self.assertIn("position:sticky!important", text)
        self.assertIn("right:34px!important", text)
        self.assertIn("right:0!important", text)

    def test_browser_regression_is_registered(self):
        runner = (ROOT / "scripts" / "run_browser_regressions.py").read_text(encoding="utf-8")
        self.assertIn("revalidate_spreadsheet_visual_polish_beta1.py", runner)


if __name__ == "__main__":
    unittest.main()
