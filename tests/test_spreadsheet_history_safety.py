from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetHistorySafetyTests(unittest.TestCase):
    def test_history_controller_scopes_actions_to_sheet_and_round_trips_recovery(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const api = require('./apps/spreadsheets/history-controller.js');
if (!api || api.version !== '0.20.3.0') process.exit(10);
const history = api.create({limit:3});
history.push({kind:'cells',entries:[{ref:'A1',before:null,after:{v:'one'}}]}, 0);
history.push({kind:'cells',entries:[{ref:'B2',before:null,after:{v:'two'}}]}, 1);
if (!history.canUndo() || history.canRedo()) process.exit(11);
let action = history.undo();
if (!action || action.sheetIndex !== 1 || action.entries[0].ref !== 'B2') process.exit(12);
if (!history.canRedo()) process.exit(13);
const exported = history.exportState();
const restored = api.create({limit:3});
restored.importState(exported);
action = restored.redo();
if (!action || action.sheetIndex !== 1 || action.entries[0].after.v !== 'two') process.exit(14);
action.after = {corrupted:true};
const safe = restored.undo();
if (!safe || safe.entries[0].after.v !== 'two') process.exit(15);
restored.push({kind:'merges',before:[],after:['A1:B2']}, 2);
restored.push({kind:'cells',entries:[]}, 3);
restored.push({kind:'cells',entries:[]}, 4);
const limited = restored.exportState();
if (limited.undo.length !== 3 || limited.undo[0].sheetIndex !== 2) process.exit(16);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_spreadsheet_loads_history_before_app_and_harnesses_match(self):
        html = (ROOT / "apps/spreadsheets/index.html").read_text(encoding="utf-8")
        history = "history-controller.js?v=1.0.0-beta.6"
        app = "app.js?v=1.0.0-beta.6"
        self.assertIn(history, html)
        self.assertIn(app, html)
        self.assertLess(html.index(history), html.index(app))
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("./apps/spreadsheets/history-controller.js", worker)
        for relative in (
            "tests/browser/revalidate_cross_workspace_isolation.py",
            "tests/browser/revalidate_launch_and_offline_modes.py",
            "tests/browser/revalidate_transactional_open_failures.py",
            "tests/browser/revalidate_workspace_consistency.py",
            "tests/browser/revalidate_xls_zero_formula_display.py",
            "tests/browser/revalidate_xlsx_three_eras.py",
        ):
            harness = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("apps/spreadsheets/history-controller.js", harness, relative)
            self.assertLess(
                harness.index("apps/spreadsheets/history-controller.js"),
                harness.index("apps/spreadsheets/app.js"),
                relative,
            )

    def test_app_history_is_sheet_scoped_recalculated_and_formula_guarded(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        for marker in (
            "InkDOSSpreadsheetHistory.create({limit:80})",
            "history.push(action,book.active)",
            "Number(action.sheetIndex)",
            "restoreCells(action.entries||[],useAfter,target)",
            "target.merges=[...(useAfter?action.after:action.before||[])]",
            "recalculateWorkbook();renderGrid();refreshSelection();markDirty(true)",
            "formulaSafety.guardHistory(toast)",
        ):
            self.assertIn(marker, text)
        self.assertNotIn("undoStack=[]", text)
        self.assertNotIn("redoStack=[]", text)

    def test_recovery_schema_preserves_history_after_restore(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        self.assertIn("schemaVersion:3", text)
        self.assertIn("history:history.exportState()", text)
        self.assertIn("history.importState(payload.history||{})", text)
        self.assertIn("history.reset();refreshUndoState()", text)

    def test_formula_safety_guards_history_while_drafts_exist(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const api = require('./apps/spreadsheets/formula-safety.js');
if (!api || api.version !== '0.20.3.0') process.exit(10);
let pending = true;
const safety = api.create({editor:()=>({hasPendingDrafts:()=>pending,reset:()=>{pending=false;}})});
let message = '';
if (!safety.guardHistory(value=>{message=value;})) process.exit(11);
if (!message.includes('Undo or Redo')) process.exit(12);
pending = false;
if (safety.guardHistory(()=>{})) process.exit(13);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
