from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetFormulaSafetyTests(unittest.TestCase):
    def test_safety_coordinator_is_dom_free_and_deterministic(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const api = require('./apps/spreadsheets/formula-safety.js');
if (!api || api.version !== '0.20.3.0') process.exit(10);
let pending = false;
let resets = 0;
const coordinator = api.create({editor:()=>({
  hasPendingDrafts:()=>pending,
  reset:()=>{pending=false;resets+=1;}
})});
if (coordinator.hasDrafts()) process.exit(11);
if (!coordinator.hasUnsaved(true)) process.exit(12);
pending = true;
if (!coordinator.hasDrafts() || !coordinator.hasUnsaved(false)) process.exit(13);
let message = '';
if (!coordinator.guardSave(value=>{message=value;})) process.exit(14);
if (!message.includes('Confirm or cancel formula drafts')) process.exit(15);
message = '';
if (!coordinator.guardHistory(value=>{message=value;})) process.exit(16);
if (!message.includes('Undo or Redo')) process.exit(17);
coordinator.reset();
if (pending || resets !== 1 || coordinator.hasDrafts()) process.exit(18);
if (coordinator.guardSave(()=>{}) || coordinator.guardHistory(()=>{})) process.exit(19);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_safety_runtime_loads_before_spreadsheet_app_and_is_precached(self):
        html = (ROOT / "apps/spreadsheets/index.html").read_text(encoding="utf-8")
        safety = "formula-safety.js?v=1.0.0-beta.7"
        app = "app.js?v=1.0.0-beta.7"
        self.assertIn(safety, html)
        self.assertIn(app, html)
        self.assertLess(html.index(safety), html.index(app))
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("./apps/spreadsheets/formula-safety.js", worker)
        for relative in (
            "tests/browser/revalidate_cross_workspace_isolation.py",
            "tests/browser/revalidate_launch_and_offline_modes.py",
            "tests/browser/revalidate_transactional_open_failures.py",
            "tests/browser/revalidate_workspace_consistency.py",
            "tests/browser/revalidate_xls_zero_formula_display.py",
            "tests/browser/revalidate_xlsx_three_eras.py",
        ):
            harness = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("formula-safety.js", harness, relative)
            self.assertLess(harness.index("formula-safety.js"), harness.index("apps/spreadsheets/app.js"), relative)

    def test_session_reset_clears_all_pending_drafts(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const api = require('./apps/spreadsheets/formula-session.js');
if (!api || api.version !== '0.20.3.0') process.exit(10);
const session = api.createSession();
const first = { id: 'A1' };
const second = { id: 'B2' };
session.start({ cell:first, reference:'A1', key:'Sheet1!A1', value:'=SU', caret:3 });
session.suspend();
session.start({ cell:second, reference:'B2', key:'Sheet1!B2', value:'=A1+', caret:4 });
if (!session.hasDrafts() || session.drafts.size !== 2) process.exit(11);
const before = session.reset();
if (!before.active || before.targetReference !== 'B2') process.exit(12);
if (session.hasDrafts() || session.drafts.size !== 0) process.exit(13);
if (session.state.active || session.state.cell !== null) process.exit(14);
if (session.state.targetReference || session.state.targetKey || session.state.value || session.state.caret !== 0) process.exit(15);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_editor_exposes_pending_and_reset_boundary(self):
        text = (ROOT / "apps/spreadsheets/formula-editor.js").read_text(encoding="utf-8")
        self.assertIn("hasPendingDrafts: function () { return session.hasDrafts(); }", text)
        self.assertIn("function reset()", text)
        self.assertIn("session.reset();", text)
        self.assertIn("reset,", text)

    def test_app_guards_save_open_new_and_beforeunload(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        for marker in (
            "InkDOSSpreadsheetFormulaSafety.create",
            "formulaSafety.hasUnsaved(dirty)",
            "formulaSafety.guardSave(toast)",
            "formulaSafety.reset();revokeWorkbookObjectUrls(book);book=nextBook",
            "if(!formulaSafety.hasUnsaved(dirty))return;e.preventDefault();e.returnValue=''",
        ):
            self.assertIn(marker, text)

    def test_failed_open_keeps_formula_drafts_until_parse_succeeds(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        parse = "const nextBook=legacy?await LocalXLS.parseWorkbook(buf,file.name):await LocalXLSX.parseWorkbook(buf,file.name);"
        reset = "formulaSafety.reset();revokeWorkbookObjectUrls(book);book=nextBook;"
        self.assertIn(parse, text)
        self.assertIn(reset, text)
        self.assertLess(text.index(parse), text.index(reset, text.index(parse)))

    def test_save_guard_runs_before_xlsx_serialization(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        start = text.index("async function prepareSave()")
        guard = text.index("formulaSafety.guardSave(toast)", start)
        serialize = text.index("LocalXLSX.saveCopy(book)", start)
        self.assertLess(guard, serialize)


if __name__ == "__main__":
    unittest.main()
