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

    def test_entry_page_loads_controller_after_core_app(self):
        html = (
            ROOT / "apps" / "spreadsheets" / "index.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'formula-reference.css?v=0.19.4.9',
            html,
        )
        self.assertIn(
            'id="addFormulaRangeBtn"',
            html,
        )
        self.assertIn(
            'id="formulaReferenceStatus"',
            html,
        )
        self.assertIn(
            'id="formulaSuggestions"',
            html,
        )

        app_position = html.index(
            '<script src="app.js"></script>'
        )
        helper_position = html.index(
            'formula-reference.js?v=0.19.4.9'
        )
        self.assertLess(app_position, helper_position)

    def test_controller_preserves_target_and_intercepts_grid_selection(self):
        runtime = (
            ROOT
            / "apps"
            / "spreadsheets"
            / "formula-reference.js"
        ).read_text(encoding="utf-8")

        for marker in (
            "stopImmediatePropagation",
            "event.ctrlKey",
            "event.metaKey",
            "state.nextAdditive",
            "state.targetReference",
            "formula.focus",
            "setSelectionRange",
            "dataset.formulaReferenceMode",
            "pointermove",
            "pointerup",
            "addFormulaRangeBtn",
            "formula-target-cell",
            "formula-reference-range",
        ):
            self.assertIn(marker, runtime)

    def test_styles_distinguish_target_and_multiple_references(self):
        styles = (
            ROOT
            / "apps"
            / "spreadsheets"
            / "formula-reference.css"
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
            "'./apps/spreadsheets/formula-reference.css'",
            worker,
        )
        self.assertIn(
            "'./apps/spreadsheets/formula-reference.js'",
            worker,
        )
        self.assertRegex(
            worker,
            r"const CACHE_NAME=['\"]inkdesk-shell-v[^'\"]+['\"];",
        )

    def test_manifest_exposes_formula_reference_contract(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(
                encoding="utf-8"
            )
        )

        contract = manifest[
            "spreadsheetFormulaReferenceSystem"
        ]
        self.assertEqual(contract["version"], "0.19.4.9")
        self.assertEqual(contract["confirmation"], "Enter")
        self.assertEqual(contract["cancellation"], "Escape")
        self.assertIn(
            "ctrl-or-command-discontinuous",
            contract["selectionModes"],
        )
        self.assertIn(
            "touch-add-range-button",
            contract["selectionModes"],
        )

        capabilities = set(
            manifest["capabilities"]["spreadsheets"]
        )
        self.assertIn(
            "xlsx-formula-mouse-reference-selection",
            capabilities,
        )
        self.assertIn(
            "xlsx-formula-drag-range-selection",
            capabilities,
        )
        self.assertIn(
            "xlsx-formula-discontinuous-reference-selection",
            capabilities,
        )
        self.assertIn(
            "xlsx-formula-target-cell-preservation",
            capabilities,
        )

    def test_formula_reference_pure_runtime(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
require('./apps/spreadsheets/formula-reference.js');
const api = globalThis.InkDeskFormulaReferences;

if (!api || api.version !== '0.19.4.9') process.exit(10);
if (api.encodeColumn(0) !== 'A') process.exit(11);
if (api.encodeColumn(25) !== 'Z') process.exit(12);
if (api.encodeColumn(26) !== 'AA') process.exit(13);
if (api.encodeCell(1, 1) !== 'B2') process.exit(14);

if (
  api.formatRange(
    { r: 1, c: 1 },
    { r: 11, c: 1 }
  ) !== 'B2:B12'
) process.exit(15);

const first = api.insertReference(
  '=SUM(',
  5,
  5,
  'B2:B12',
  { additive: false }
);

if (first.value !== '=SUM(B2:B12)') process.exit(16);
if (first.caret !== '=SUM(B2:B12'.length) process.exit(17);

const second = api.insertReference(
  first.value,
  first.caret,
  first.caret,
  'D4',
  { additive: true }
);

if (second.value !== '=SUM(B2:B12,D4)') process.exit(18);

const replacement = api.insertReference(
  first.value,
  first.caret,
  first.caret,
  'C1:C5',
  { additive: false }
);

if (replacement.value !== '=SUM(C1:C5)') process.exit(19);

const arithmetic = api.insertReference(
  '=A1+',
  4,
  4,
  'B2',
  { additive: true }
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
            (ROOT / "package.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            package["scripts"][
                "test:spreadsheet-formula-references"
            ],
            (
                "python3 -m unittest "
                "tests.test_spreadsheet_formula_references"
            ),
        )


if __name__ == "__main__":
    unittest.main()
