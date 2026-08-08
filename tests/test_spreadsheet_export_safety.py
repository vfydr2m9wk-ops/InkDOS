from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetExportSafetyTests(unittest.TestCase):
    def test_download_flushes_recovery_before_dispatch(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        start = text.index("async function download()")
        end = text.index("async function newWorkbook()", start)
        block = text[start:end]
        self.assertIn("await recovery.flush()", block)
        self.assertIn("InkDeskRuntime.requestDownload(pendingBlob,fileName)", block)
        self.assertLess(block.index("await recovery.flush()"), block.index("InkDeskRuntime.requestDownload(pendingBlob,fileName)"))

    def test_unverified_download_does_not_clear_dirty_or_recovery(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        start = text.index("async function download()")
        end = text.index("async function newWorkbook()", start)
        block = text[start:end]
        self.assertNotIn("markDirty(false)", block)
        self.assertNotIn("recovery.markClean()", block)
        self.assertNotIn("recovery.clearSnapshots()", block)
        self.assertNotIn("recovery.discardCurrent()", block)

    def test_download_message_requires_user_verification_before_discard(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        self.assertIn("confirm the XLSX in Downloads before discarding this workbook", text)

    def test_browser_recovery_asserts_post_download_protection(self):
        text = (ROOT / "tests/browser/revalidate_v0202_local_recovery.py").read_text(encoding="utf-8")
        for marker in (
            "protected_after_download",
            "items.length>=1",
            'dirtyVisible: !document.querySelector(\'#dirtyDot\').hidden',
            "titleWarns: document.title.includes(' •')",
            "cleared unsaved/recovery protection before the copy was verified",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
