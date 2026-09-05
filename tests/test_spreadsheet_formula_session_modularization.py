from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetFormulaSessionModularizationTests(unittest.TestCase):
    def test_session_module_is_loaded_between_model_and_interaction(self):
        html = (ROOT / "apps/spreadsheets/index.html").read_text(encoding="utf-8")
        model = "formula-model.js?v=1.0.0-beta.6"
        session = "formula-session.js?v=1.0.0-beta.6"
        reference = "formula-reference.js?v=1.0.0-beta.6"
        editor = "formula-editor.js?v=1.0.0-beta.6"
        for asset in (model, session, reference, editor):
            self.assertIn(asset, html)
        self.assertLess(html.index(model), html.index(session))
        self.assertLess(html.index(session), html.index(reference))
        self.assertLess(html.index(session), html.index(editor))

        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("'./apps/spreadsheets/formula-session.js'", worker)

    def test_session_owns_draft_map_and_lifecycle_mutations(self):
        session = (ROOT / "apps/spreadsheets/formula-session.js").read_text(encoding="utf-8")
        editor = (ROOT / "apps/spreadsheets/formula-editor.js").read_text(encoding="utf-8")
        for marker in (
            "const drafts = new Map()",
            "function rememberDraft()",
            "function start(input)",
            "function suspend()",
            "function prepareCommit(balanceFormula)",
            "function prepareCancel()",
        ):
            self.assertIn(marker, session)
        self.assertIn("FormulaSession.createSession({ clamp })", editor)
        self.assertIn("session.prepareCommit(balanceFormula)", editor)
        self.assertIn("session.prepareCancel()", editor)
        self.assertNotIn("const drafts = new Map()", editor)
        self.assertNotIn("drafts.set(", editor)

    def test_session_lifecycle_is_deterministic_without_dom(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const api = require('./apps/spreadsheets/formula-session.js');
if (!api || api.version !== '0.20.3.0') process.exit(10);
const session = api.createSession();
const cell = { id: 'C1' };
let opened = session.start({
  cell,
  reference: 'C1',
  key: 'Sheet1!C1',
  value: '=SU',
  caret: 3,
  originalDisplay: '12',
  originalFormulaValue: '12'
});
if (!opened || opened.resumed || !session.state.active) process.exit(11);
if (session.state.value !== '=SU' || session.state.caret !== 3) process.exit(12);
session.update('=SUM(A1:A2', 10);
const suspended = session.suspend();
if (!suspended || suspended.value !== '=SUM(A1:A2' || session.state.active) process.exit(13);
if (!session.savedFor('Sheet1!C1')) process.exit(14);
opened = session.start({ cell, reference: 'C1', key: 'Sheet1!C1', value: '=IGNORED', caret: 8 });
if (!opened.resumed || opened.value !== '=SUM(A1:A2') process.exit(15);
const committed = session.prepareCommit((value) => value + ')');
if (!committed || committed.value !== '=SUM(A1:A2)' || committed.caret !== 11) process.exit(16);
if (session.savedFor('Sheet1!C1')) process.exit(17);
session.clearActive();
if (session.state.active || session.state.cell !== null) process.exit(18);

session.start({
  cell,
  reference: 'D4',
  key: 'Sheet1!D4',
  value: '=S',
  caret: 2,
  originalDisplay: 'old',
  originalFormulaValue: 'old'
});
const cancelled = session.prepareCancel();
if (!cancelled || cancelled.originalDisplay !== 'old') process.exit(19);
if (session.savedFor('Sheet1!D4')) process.exit(20);
session.clearActive();
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_session_normalization_and_caret_clamping_are_stable(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const api = require('./apps/spreadsheets/formula-session.js');
if (api.normalizeDraft('=A1\r\n+B1') !== '=A1+B1') process.exit(10);
const session = api.createSession();
const cell = {};
session.start({ cell, reference: 'A1', key: 'Sheet!A1', value: '=A1', caret: 99 });
if (session.state.caret !== 3) process.exit(11);
session.update('=B2\n+C3', -50);
if (session.state.value !== '=B2+C3' || session.state.caret !== 0) process.exit(12);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_architecture_ratchet_shrinks_editor_and_session_stays_bounded(self):
        editor_lines = len((ROOT / "apps/spreadsheets/formula-editor.js").read_text(encoding="utf-8").splitlines())
        session_lines = len((ROOT / "apps/spreadsheets/formula-session.js").read_text(encoding="utf-8").splitlines())
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        self.assertLess(editor_lines, 616)
        self.assertLessEqual(session_lines, policy["extensions"][".js"]["newFileMaxLines"])
        self.assertEqual(
            policy["grandfatheredDebt"]["apps/spreadsheets/formula-editor.js"]["maxLines"],
            editor_lines,
        )
        self.assertNotIn("apps/spreadsheets/formula-session.js", policy["grandfatheredDebt"])

    def test_package_script_is_registered(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(
            package["scripts"]["test:spreadsheet-formula-lifecycle"],
            "python3 -m unittest tests.test_spreadsheet_formula_session_modularization",
        )


if __name__ == "__main__":
    unittest.main()
