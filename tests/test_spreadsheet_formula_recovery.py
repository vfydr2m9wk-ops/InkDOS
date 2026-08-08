from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetFormulaRecoveryTests(unittest.TestCase):
    def test_formula_session_exports_and_imports_serializable_drafts(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const api = require('./apps/spreadsheets/formula-session.js');
if (!api || api.version !== '0.20.3.0') process.exit(10);
const session = api.createSession();
session.start({cell:{}, reference:'B2', key:'Sheet1!B2', value:'=SU\n', caret:99});
session.suspend();
const exported = session.exportDrafts();
if (exported.length !== 1) process.exit(11);
if (exported[0].key !== 'Sheet1!B2' || exported[0].reference !== 'B2') process.exit(12);
if (exported[0].value !== '=SU' || exported[0].caret !== 3) process.exit(13);
const restored = api.createSession();
restored.importDrafts(exported.concat([{key:'', reference:'A1', value:'bad'}]));
if (restored.state.active || restored.state.cell !== null) process.exit(14);
const draft = restored.savedFor('Sheet1!B2');
if (!draft || draft.value !== '=SU' || draft.caret !== 3) process.exit(15);
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_editor_exposes_recovery_boundary_and_notifies_all_lifecycle_changes(self):
        text = (ROOT / "apps/spreadsheets/formula-editor.js").read_text(encoding="utf-8")
        for marker in (
            "function snapshotDrafts()",
            "function restoreDrafts(entries)",
            "session.exportDrafts()",
            "session.importDrafts(entries)",
            "notifySessionChange(opened.resumed ? 'resume' : 'start')",
            "notifySessionChange('suspend')",
            "notifySessionChange('update')",
            "notifySessionChange('commit')",
            "notifySessionChange('cancel')",
            "notifySessionChange('restore')",
        ):
            self.assertIn(marker, text)

    def test_spreadsheet_recovery_schema_carries_formula_drafts(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        self.assertIn("schemaVersion:3", text)
        self.assertIn("snapshotDrafts", text)
        self.assertIn("formulaDrafts", text)
        self.assertIn("history:history.exportState()", text)
        self.assertIn("history.importState(payload.history||{})", text)
        self.assertIn("editor.restoreDrafts(payload.formulaDrafts||[])", text)
        self.assertIn("inkdesk:formula-session-change", text)
        self.assertIn("recovery.clearSnapshots()", text)

    def test_confirmed_workbook_replacement_discards_old_recovery_only_after_parse(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        parse = "const nextBook=legacy?await LocalXLS.parseWorkbook(buf,file.name):await LocalXLSX.parseWorkbook(buf,file.name);"
        discard = "if(recovery)await recovery.discardCurrent();"
        reset = "formulaSafety.reset();revokeWorkbookObjectUrls(book);book=nextBook;"
        self.assertIn(parse, text)
        self.assertIn(discard, text)
        self.assertIn(reset, text)
        parse_pos = text.index(parse)
        discard_pos = text.index(discard, parse_pos)
        reset_pos = text.index(reset, discard_pos)
        self.assertLess(parse_pos, discard_pos)
        self.assertLess(discard_pos, reset_pos)
        self.assertIn("async function newWorkbook()", text)

    def test_shared_recovery_has_generation_barrier_and_snapshot_only_clear(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        for marker in (
            "let dirty=false,revision=0,generation=0,destroyed=false",
            "const capturedRevision=revision,capturedGeneration=generation",
            "capturedGeneration!==generation",
            "capturedDocumentKey!==documentKey",
            "async function clearSnapshots()",
            "deleteSnapshotsOnly(moduleName,key,sessionId)",
            "const key=documentKey,pending=writing;generation+=1",
            "clearSnapshots,markClean,discardCurrent",
        ):
            self.assertIn(marker, text)

    def test_browser_recovery_regression_covers_uncommitted_formula_and_write_barrier(self):
        text = (ROOT / "tests/browser/revalidate_v0202_local_recovery.py").read_text(encoding="utf-8")
        for marker in (
            'formula_draft = "=SU"',
            "snapshotDrafts()",
            "recovery_write_barrier_case",
            "module: 'recovery-race'",
            "releaseSerialize({marker:'old'})",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
