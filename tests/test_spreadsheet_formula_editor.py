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
            "apps/spreadsheets/formula-editor.js",
            "apps/spreadsheets/formula-editor.css",
            "docs/SPREADSHEET_FORMULA_EDITOR.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_entry_page_loads_editor_after_reference_controller(self):
        html = (
            ROOT / "apps" / "spreadsheets" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "formula-editor.css?v=0.19.4.9",
            html,
        )
        self.assertIn(
            "formula-editor.js?v=0.19.4.9",
            html,
        )

        reference_position = html.index(
            "formula-reference.js?v=0.19.4.9"
        )
        editor_position = html.index(
            "formula-editor.js?v=0.19.4.9"
        )
        self.assertLess(reference_position, editor_position)

        formula_row_start = html.index(
            '<section class="formula-row">'
        )
        formula_row_end = html.index(
            "</section>",
            formula_row_start,
        )
        formula_row = html[
            formula_row_start:formula_row_end
        ]

        self.assertNotIn(
            'id="formulaReferenceStatus"',
            formula_row,
        )
        self.assertIn(
            'id="formulaReferenceStatus"',
            html[formula_row_end:],
        )

    def test_editor_reserves_enter_for_confirmation(self):
        runtime = (
            ROOT
            / "apps"
            / "spreadsheets"
            / "formula-editor.js"
        ).read_text(encoding="utf-8")

        for marker in (
            "event.key === 'Tab'",
            "event.key === 'Enter'",
            "event.key === 'Escape'",
            "Enter never accepts a suggestion",
            "balanceFormula(currentValue())",
            "openCellEditor(cell, '=', 1)",
            "event.key === 'F2'",
            "'dblclick'",
            "cell-formula-editor",
            "setValueFromReference",
        ):
            self.assertIn(marker, runtime)

    def test_reference_controller_uses_editor_selection(self):
        runtime = (
            ROOT
            / "apps"
            / "spreadsheets"
            / "formula-reference.js"
        ).read_text(encoding="utf-8")

        for marker in (
            "const VERSION = '0.19.4.9'",
            "function formulaEditor()",
            "editor.isActive()",
            "editor.getSelection()",
            "editor.setValueFromReference(result)",
            "autoClose: false",
            "editor.focus()",
        ):
            self.assertIn(marker, runtime)

    def test_formula_bar_is_larger_and_status_is_below(self):
        shared = (
            ROOT / "shared" / "ui" / "workspace-layout.css"
        ).read_text(encoding="utf-8")

        editor = (
            ROOT
            / "apps"
            / "spreadsheets"
            / "formula-editor.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "height: 46px !important",
            shared,
        )
        self.assertIn(
            "46px -",
            shared,
        )
        self.assertIn(
            "> footer .formula-reference-status",
            editor,
        )
        self.assertIn(
            ".cell-formula-editor",
            editor,
        )

    def test_manifest_exposes_formula_editor_contract(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(
                encoding="utf-8"
            )
        )

        editor = manifest[
            "spreadsheetFormulaEditorSystem"
        ]
        self.assertEqual(editor["version"], "0.19.4.9")
        self.assertEqual(editor["formulaConfirm"], "Enter")
        self.assertEqual(editor["formulaCancel"], "Escape")
        self.assertIn("=", editor["directCellStart"])
        self.assertIn("Tab", editor["suggestionAccept"])

        reference = manifest[
            "spreadsheetFormulaReferenceSystem"
        ]
        self.assertEqual(reference["version"], "0.19.4.9")
        self.assertFalse(
            reference["autoCloseDuringRangeSelection"]
        )
        self.assertTrue(
            reference["parenthesesBalancedOnCommit"]
        )

    def test_service_worker_caches_formula_editor(self):
        worker = (ROOT / "service-worker.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "'./apps/spreadsheets/formula-editor.css'",
            worker,
        )
        self.assertIn(
            "'./apps/spreadsheets/formula-editor.js'",
            worker,
        )
        self.assertIn("0.19.4.9", worker)

    def test_pure_suggestion_and_formula_runtime(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
require('./apps/spreadsheets/formula-editor.js');
const api = globalThis.InkDeskFormulaEditor;

if (!api || api.version !== '0.19.4.9') process.exit(10);

const empty = api.suggestionContext('=', 1);
if (!empty || empty.query !== '') process.exit(11);

const sum = api.suggestionContext('=SU', 3);
if (!sum || sum.query !== 'SU') process.exit(12);

const cellStart = api.suggestionContext('=SUM(A', 6);
if (cellStart !== null) process.exit(13);

const nested = api.suggestionContext('=IF(A1>0,SU', 12);
if (!nested || nested.query !== 'SU') process.exit(14);

if (api.balanceFormula('=SUM(A1') !== '=SUM(A1)') {
  process.exit(15);
}

if (
  api.balanceFormula('=IF(A1>0,SUM(B1:B4)') !==
  '=IF(A1>0,SUM(B1:B4))'
) {
  process.exit(16);
}

const inserted = api.applyFunctionSuggestion(
  '=SU',
  1,
  3,
  'SUM'
);

if (inserted.value !== '=SUM(') process.exit(17);
if (inserted.caret !== 5) process.exit(18);

const matches = api.matchingFunctions(sum);
if (!matches.some(item => item[0] === 'SUM')) {
  process.exit(19);
}
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

    def test_package_script_is_registered(self):
        package = json.loads(
            (ROOT / "package.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            package["scripts"][
                "test:spreadsheet-formula-editor"
            ],
            (
                "python3 -m unittest "
                "tests.test_spreadsheet_formula_editor"
            ),
        )


if __name__ == "__main__":
    unittest.main()
