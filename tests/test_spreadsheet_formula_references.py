from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetFormulaReferenceTests(unittest.TestCase):
    def test_required_assets_exist(self):
        for relative in (
            "apps/spreadsheets/index.html",
            "apps/spreadsheets/formula-reference.js",
            "apps/spreadsheets/formula-reference.css",
            "docs/SPREADSHEET_FORMULA_REFERENCES.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_entry_page_loads_reference_before_formula_session(self):
        html = (
            ROOT / "apps" / "spreadsheets" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'formula-reference.css?v=0.20.3.0',
            html,
        )
        self.assertIn('id="addFormulaRangeBtn"', html)
        self.assertIn('id="formulaReferenceStatus"', html)
        self.assertIn('id="formulaSuggestions"', html)

        core_position = html.index('<script src="app.js?v=0.20.3.0"></script>')
        model_position = html.index('formula-model.js?v=0.20.3.0')
        session_position = html.index('formula-session.js?v=0.20.3.0')
        reference_position = html.index(
            'formula-reference.js?v=0.20.3.0'
        )
        editor_position = html.index(
            'formula-editor.js?v=0.20.3.0'
        )
        self.assertLess(core_position, model_position)
        self.assertLess(model_position, session_position)
        self.assertLess(session_position, reference_position)
        self.assertLess(reference_position, editor_position)

    def test_controller_intercepts_grid_and_uses_persistent_editor(self):
        runtime = (
            ROOT / "apps" / "spreadsheets" / "formula-reference.js"
        ).read_text(encoding="utf-8")

        for marker in (
            "stopImmediatePropagation",
            "event.ctrlKey",
            "event.metaKey",
            "state.nextAdditive",
            "state.targetReference",
            "currentEditor.canSelectReference()",
            "currentEditor.shouldAppendReference()",
            "currentEditor.getSelection()",
            "editor()?.applyReference(result)",
            "editor()?.focus()",
            "dataset.formulaReferenceMode",
            "pointermove",
            "pointerup",
            "Click or drag another cell",
        ):
            self.assertIn(marker, runtime)

    def test_styles_distinguish_target_and_multiple_references(self):
        styles = (
            ROOT / "apps" / "spreadsheets" / "formula-reference.css"
        ).read_text(encoding="utf-8")

        self.assertIn(".cell.formula-target-cell", styles)
        self.assertIn(".cell.formula-reference-range", styles)
        for index in range(1, 7):
            self.assertIn(
                f".cell.formula-reference-color-{index}",
                styles,
            )
        self.assertIn(".formula-range-add", styles)

    def test_service_worker_caches_formula_reference_assets(self):
        worker = (ROOT / "service-worker.js").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "'./apps/spreadsheets/formula-reference.css'", worker
        )
        self.assertIn(
            "'./apps/spreadsheets/formula-reference.js'", worker
        )
        self.assertRegex(
            worker,
            r"const CACHE_NAME=['\"]inkdesk-shell-v[^'\"]+['\"];",
        )

    def test_manifest_exposes_reference_contract(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(encoding="utf-8")
        )
        contract = manifest["spreadsheetFormulaReferenceSystem"]
        self.assertEqual(contract["version"], "0.20.1")
        self.assertEqual(contract["confirmation"], "Enter")
        self.assertEqual(contract["cancellation"], "Escape")
        self.assertTrue(contract["successiveClicksAppend"])
        self.assertFalse(contract["autoCloseDuringRangeSelection"])
        self.assertTrue(contract["parenthesesBalancedOnCommit"])
        self.assertIn(
            "ctrl-or-command-discontinuous",
            contract["selectionModes"],
        )

    def test_formula_reference_pure_runtime(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
require('./apps/spreadsheets/formula-reference.js');
const api = globalThis.InkDeskFormulaReferences;
if (!api || api.version !== '0.20.1') process.exit(10);
if (api.encodeColumn(0) !== 'A') process.exit(11);
if (api.encodeColumn(25) !== 'Z') process.exit(12);
if (api.encodeColumn(26) !== 'AA') process.exit(13);
if (api.encodeCell(1, 1) !== 'B2') process.exit(14);
if (api.formatRange({r:1,c:1},{r:11,c:1}) !== 'B2:B12') process.exit(15);

const first = api.insertReference(
  '=SUM(', 5, 5, 'B2:B12',
  { additive: false, replaceToken: false }
);
if (first.value !== '=SUM(B2:B12') process.exit(16);
if (first.caret !== first.value.length) process.exit(17);

const second = api.insertReference(
  first.value, first.caret, first.caret, 'D4',
  { additive: true, replaceToken: false }
);
if (second.value !== '=SUM(B2:B12,D4') process.exit(18);

const replacement = api.insertReference(
  first.value, first.caret, first.caret, 'C1:C5',
  { additive: false, replaceToken: true }
);
if (replacement.value !== '=SUM(C1:C5') process.exit(19);

const arithmetic = api.insertReference(
  '=A1+', 4, 4, 'B2',
  { additive: false, replaceToken: false }
);
if (arithmetic.value !== '=A1+B2') process.exit(20);
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
            (ROOT / "package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            package["scripts"]["test:spreadsheet-formula-references"],
            "python3 -m unittest tests.test_spreadsheet_formula_references",
        )


if __name__ == "__main__":
    unittest.main()
