from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetFormulaModelModularizationTests(unittest.TestCase):
    def test_model_is_loaded_before_formula_interaction_controllers(self):
        html = (ROOT / "apps/spreadsheets/index.html").read_text(encoding="utf-8")
        model = 'formula-model.js?v=0.20.2.22'
        session = 'formula-session.js?v=0.20.2.22'
        reference = 'formula-reference.js?v=0.20.2.22'
        editor = 'formula-editor.js?v=0.20.2.22'
        self.assertIn(model, html)
        self.assertLess(html.index(model), html.index(session))
        self.assertLess(html.index(session), html.index(reference))
        self.assertLess(html.index(model), html.index(editor))

        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("'./apps/spreadsheets/formula-model.js'", worker)

    def test_formula_model_owns_pure_syntax_helpers(self):
        model = (ROOT / "apps/spreadsheets/formula-model.js").read_text(encoding="utf-8")
        editor = (ROOT / "apps/spreadsheets/formula-editor.js").read_text(encoding="utf-8")
        for marker in (
            "const FUNCTIONS = Object.freeze([",
            "function parenthesisDepth(value)",
            "function suggestionContext(value, cursor)",
            "function matchingFunctions(context)",
            "function formulaCanSelectReference(value, cursor)",
            "function shouldAppendReference(value, cursor)",
            "function formulaIsComplete(value)",
        ):
            self.assertIn(marker, model)
            self.assertNotIn(marker, editor)
        self.assertIn("global.InkDeskSpreadsheetFormulaModel", model)
        self.assertIn("require('./formula-model.js')", editor)
        self.assertIn("functions: FUNCTIONS", editor)

    def test_architecture_ratchet_shrinks_editor_without_creating_new_debt(self):
        editor_lines = len((ROOT / "apps/spreadsheets/formula-editor.js").read_text(encoding="utf-8").splitlines())
        model_lines = len((ROOT / "apps/spreadsheets/formula-model.js").read_text(encoding="utf-8").splitlines())
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        self.assertLess(editor_lines, 616)
        self.assertLessEqual(model_lines, policy["extensions"][".js"]["newFileMaxLines"])
        self.assertEqual(policy["grandfatheredDebt"]["apps/spreadsheets/formula-editor.js"]["maxLines"], editor_lines)
        self.assertNotIn("apps/spreadsheets/formula-model.js", policy["grandfatheredDebt"])

    def test_formula_model_edge_cases_are_deterministic(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const api = require('./apps/spreadsheets/formula-model.js');
if (!api || api.version !== '0.20.2.22') process.exit(10);
if (api.encodeColumn(0) !== 'A' || api.encodeColumn(25) !== 'Z' || api.encodeColumn(26) !== 'AA') process.exit(11);
if (api.parenthesisDepth('=IF(A1="(",SUM(B1:B2),0') !== 1) process.exit(12);
if (api.balanceFormula('=SUM(A1:A10') !== '=SUM(A1:A10)') process.exit(13);
if (api.suggestionContext('=', 1) !== null || api.suggestionContext('=S', 2) !== null) process.exit(14);
const context = api.suggestionContext('=SU', 3);
if (!context || context.query !== 'SU' || context.start !== 1 || !context.root) process.exit(15);
const matches = api.matchingFunctions(context);
if (!matches.length || matches[0][0] !== 'SUM' || matches.length > api.maxSuggestions) process.exit(16);
const inserted = api.applyFunctionSuggestion('=SU', 1, 3, 'sum');
if (inserted.value !== '=SUM(' || inserted.caret !== 5) process.exit(17);
if (api.formulaCanSelectReference('=S', 2)) process.exit(18);
if (!api.formulaCanSelectReference('=SUM(', 5)) process.exit(19);
if (!api.shouldAppendReference('=SUM(A1', 7)) process.exit(20);
if (!api.formulaIsComplete('=A1+B1')) process.exit(21);
if (api.formulaIsComplete('=SUM(A1:A2')) process.exit(22);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_formula_editor_public_helper_api_remains_compatible(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
require('./apps/spreadsheets/formula-editor.js');
const api = globalThis.InkDeskFormulaEditor;
if (!api || api.version !== '0.20.0') process.exit(10);
if (api.encodeColumn(26) !== 'AA') process.exit(11);
if (api.balanceFormula('=SUM(A1:A2') !== '=SUM(A1:A2)') process.exit(12);
const context = api.suggestionContext('=AV', 3);
if (!context || context.query !== 'AV') process.exit(13);
if (!api.formulaCanSelectReference('=SUM(', 5)) process.exit(14);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_script_is_registered(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            package["scripts"]["test:spreadsheet-formula-model"],
            "python3 -m unittest tests.test_spreadsheet_formula_model_modularization",
        )


if __name__ == "__main__":
    unittest.main()
