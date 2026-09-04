from __future__ import annotations

from pathlib import Path
import subprocess
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CrossWorkspaceExportSafetyTests(unittest.TestCase):
    def test_documents_download_request_keeps_dirty_and_recovery(self):
        text = (ROOT / "apps/documents/app.js").read_text(encoding="utf-8")
        start = text.index("function offerSaveCopy(result)")
        end = text.index("function selectionBlock()", start)
        block = text[start:end]
        self.assertIn("if(recovery&&dirty)await recovery.flush()", block)
        self.assertNotIn("setDirty(false)", block)
        self.assertNotIn("recovery.markClean()", block)
        self.assertIn("DOCX remains protected", block)

    def test_presentations_flush_recovery_and_do_not_claim_verified_save(self):
        text = (ROOT / "apps/presentations/io/file-controller.js").read_text(encoding="utf-8")
        for method, next_method in (
            ("async saveImportedPptx()", "async saveNewPptx()"),
            ("async saveNewPptx()", "downloadBlob(blob, name)"),
        ):
            start = text.index(method)
            end = text.index(next_method, start)
            block = text[start:end]
            self.assertIn("await this.flushRecovery()", block)
            self.assertIn("this.downloadBlob(", block)
            self.assertLess(block.index("await this.flushRecovery()"), block.index("this.downloadBlob("))
            self.assertNotIn("this.markSaved()", block)
            self.assertNotIn("this.markRecoveryClean()", block)
        recovery = (ROOT / "apps/presentations/io/recovery-controller.js").read_text(encoding="utf-8")
        self.assertIn("flush()", recovery)
        self.assertIn("this.manager.flush()", recovery)

    def test_txt_uses_unverified_download_lifecycle(self):
        text = (ROOT / "apps/txt/app.js").read_text(encoding="utf-8")
        start = text.index("function saveDocument()")
        end = text.index("function openPicker()", start)
        block = text[start:end]
        self.assertIn("lifecycle.beginExport()", block)
        self.assertIn("lifecycle.downloadRequested(receipt)", block)
        self.assertNotIn("lifecycle.resetClean()", block)
        self.assertIn("changes remain protected until you verify the TXT copy", block)

    def test_file_lifecycle_download_request_remains_unverified_when_dirty(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")
        script = r"""
const fs=require('fs'),vm=require('vm');
const listeners={};
const window={
  addEventListener:(name,fn)=>{listeners[name]=fn},
  confirm:()=>true,
  console
};
window.window=window;
const context=vm.createContext({window,console,globalThis:window});
vm.runInContext(fs.readFileSync('shared/file-lifecycle.js','utf8'),context);
const lifecycle=window.InkDOSFileLifecycle.create();
lifecycle.sourceOpened();
lifecycle.markDirty();
if(!lifecycle.shouldWarnBeforeUnload()) throw new Error('dirty state did not warn');
lifecycle.beginExport();
lifecycle.downloadRequested({fileName:'copy.txt',bytes:7});
const snap=lifecycle.snapshot();
if(snap.state!=='download-requested-unverified') throw new Error('wrong lifecycle state: '+snap.state);
if(!snap.shouldWarnBeforeUnload) throw new Error('unverified request cleared warning');
if(!snap.hasUnverifiedChanges) throw new Error('unverified request lost revision delta');
console.log('ok');
"""
        result = subprocess.run([node, "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_existing_spreadsheet_export_policy_stays_strict(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        start = text.index("async function download()")
        end = text.index("async function newWorkbook()", start)
        block = text[start:end]
        self.assertIn("await recovery.flush()", block)
        self.assertNotIn("recovery.markClean()", block)
        self.assertNotIn("markDirty(false)", block)


if __name__ == "__main__":
    unittest.main()
