from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetFormulaEngineIntegration02031Tests(unittest.TestCase):
    def test_spreadsheet_runtime_uses_shared_safe_arithmetic_engine(self):
        app = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        self.assertIn("InkDeskFormula.evaluateArithmetic(arithmetic)", app)
        self.assertNotIn("Function" + "(", app)
        self.assertNotIn("eval" + "(", app)
        self.assertIn("^[0-9+\\-*/%^(). %]+$", app)

    def test_formula_engine_is_loaded_before_spreadsheet_app(self):
        html = (ROOT / "apps/spreadsheets/index.html").read_text(encoding="utf-8")
        engine = html.index("../../shared/formula-engine.js")
        app = html.index('app.js?v=')
        self.assertLess(engine, app)

    def test_shared_engine_keeps_required_semantics(self):
        engine = (ROOT / "shared/formula-engine.js").read_text(encoding="utf-8")
        self.assertIn("left='#DIV/0!'", engine)
        self.assertIn("current.type==='%'", engine)
        self.assertIn("current.type==='^'", engine)
        self.assertIn("function errorValue(value)", engine)
        self.assertIn("errorValue(left)||errorValue(right)", engine)


if __name__ == "__main__":
    unittest.main()
