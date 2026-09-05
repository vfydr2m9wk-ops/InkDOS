from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetFormulaEditorTests(unittest.TestCase):
    def test_required_assets_exist(self):
        for relative in (
            "apps/spreadsheets/formula-model.js",
            "apps/spreadsheets/formula-session.js",
            "apps/spreadsheets/formula-editor.js",
            "apps/spreadsheets/formula-editor.css",
            "apps/spreadsheets/formula-reference.js",
            "shared/formula-engine.js",
            "docs/SPREADSHEET_FORMULA_SESSION.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_entry_page_has_no_visible_formula_help_or_overlay(self):
        html = (ROOT / "apps/spreadsheets/index.html").read_text(encoding="utf-8")
        self.assertIn("formula-editor.js?v=1.0.0-beta.7", html)
        self.assertIn("formula-reference.js?v=1.0.0-beta.7", html)
        self.assertIn('id="formulaHint" hidden', html)
        self.assertNotIn('id="cellFormulaEditor"', html)

    def test_session_uses_the_real_cell_and_preserves_drafts(self):
        runtime = (ROOT / "apps/spreadsheets/formula-editor.js").read_text(encoding="utf-8")
        for marker in (
            "FormulaSession.createSession({ clamp })",
            "const drafts = session.drafts",
            "cell.contentEditable = 'true'",
            "formula-draft-editing",
            "Formula draft preserved",
            "resumeDraftAfterCoreSelection",
            "MutationObserver",
            "formulaCanSelectReference(state.value, state.caret)",
            "formulaIsComplete(state.value)",
            "callCoreKeydown('Enter')",
        ):
            self.assertIn(marker, runtime)
        self.assertNotIn("createElement('input')", runtime)
        self.assertNotIn("cellFormulaEditor", runtime)

    def test_suggestions_wait_for_two_letters_and_enter_confirms(self):
        runtime = (ROOT / "apps/spreadsheets/formula-editor.js").read_text(encoding="utf-8")
        model = (ROOT / "apps/spreadsheets/formula-model.js").read_text(encoding="utf-8")
        self.assertIn("match[1].length < 2", model)
        self.assertIn("event.key === 'Tab'", runtime)
        self.assertIn("event.key === 'Enter'", runtime)
        self.assertIn("commit();", runtime)

    def test_reference_module_supports_drag_and_successive_clicks(self):
        runtime = (ROOT / "apps/spreadsheets/formula-reference.js").read_text(encoding="utf-8")
        for marker in (
            "currentEditor.canSelectReference()",
            "currentEditor.shouldAppendReference()",
            "pointermove",
            "formatRange(state.drag.start, point)",
            "editor()?.applyReference(result)",
            "Click or drag another cell",
        ):
            self.assertIn(marker, runtime)

    def test_cell_size_is_not_expanded(self):
        styles = (ROOT / "apps/spreadsheets/formula-editor.css").read_text(encoding="utf-8")
        self.assertIn(".cell.formula-draft-editing", styles)
        self.assertIn("max-width: 100% !important", styles)
        self.assertIn("overflow: hidden !important", styles)
        self.assertNotIn("position: fixed;\n  z-index: 1400", styles)

    def test_manifest_exposes_persistent_session(self):
        manifest = json.loads((ROOT / "app-manifest.json").read_text(encoding="utf-8"))
        editor = manifest["spreadsheetFormulaEditorSystem"]
        self.assertEqual(editor["version"], "0.20.0")
        self.assertEqual(editor["mode"], "persistent in-cell draft session")
        self.assertTrue(editor["draftSurvivesCellSwitch"])
        self.assertEqual(editor["minimumSuggestionLetters"], 2)
        self.assertEqual(editor["formulaConfirm"], "Enter")
        self.assertEqual(editor["percentageOperator"], "postfix percentage")

    def test_pure_formula_session_helpers(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
require('./apps/spreadsheets/formula-editor.js');
const api = globalThis.InkDOSFormulaEditor;
if (!api || api.version !== '0.20.0') process.exit(10);
if (api.suggestionContext('=', 1) !== null) process.exit(11);
if (api.suggestionContext('=S', 2) !== null) process.exit(12);
const su = api.suggestionContext('=SU', 3);
if (!su || su.query !== 'SU') process.exit(13);
if (api.suggestionContext('=SUM(A', 6) !== null) process.exit(14);
if (api.formulaCanSelectReference('=S', 2)) process.exit(15);
if (!api.formulaCanSelectReference('=SUM(', 5)) process.exit(16);
if (!api.shouldAppendReference('=SUM(A1', 7)) process.exit(17);
if (api.balanceFormula('=SUM(A1:A10') !== '=SUM(A1:A10)') process.exit(18);
if (!api.formulaIsComplete('=A1+B1')) process.exit(19);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_percentage_operator_matches_spreadsheet_semantics(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
require('./shared/formula-engine.js');
const api = globalThis.InkDOSFormula;
if (Math.abs(api.evaluateArithmetic('10%') - 0.1) > 1e-12) process.exit(10);
if (Math.abs(api.evaluateArithmetic('200*10%') - 20) > 1e-12) process.exit(11);
if (Math.abs(api.evaluateArithmetic('5%+5%') - 0.1) > 1e-12) process.exit(12);
if (api.evaluateArithmetic('10/0') !== '#DIV/0!') process.exit(13);
if (api.evaluateArithmetic('10/0+1') !== '#DIV/0!') process.exit(14);
if (api.evaluateArithmetic('(10/0)+1') !== '#DIV/0!') process.exit(15);
if (api.evaluateArithmetic('10/(5-5)+2') !== '#DIV/0!') process.exit(16);
if (api.evaluateArithmetic('1+10/0') !== '#DIV/0!') process.exit(17);
if (api.evaluateArithmetic('2*(10/0)') !== '#DIV/0!') process.exit(18);
if (api.evaluateArithmetic('-(10/0)') !== '#DIV/0!') process.exit(19);
if (api.evaluateArithmetic('X+1',{resolveIdentifier:()=> '#DIV/0!'}) !== '#DIV/0!') process.exit(20);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_script_is_registered(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            package["scripts"]["test:spreadsheet-formula-session"],
            "python3 -m unittest tests.test_spreadsheet_formula_session_modularization",
        )


if __name__ == "__main__":
    unittest.main()
