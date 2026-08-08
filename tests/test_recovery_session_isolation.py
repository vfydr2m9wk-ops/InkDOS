from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RecoverySessionIsolationTests(unittest.TestCase):
    def test_shared_recovery_scopes_mutations_to_session(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        for token in (
            "sessionId=String(options.sessionId||randomKey())",
            "function sameSession(item,sessionId)",
            "deleteSnapshotsOnly(moduleName,documentKey,sessionId)",
            "sessionId:capturedSessionId",
            "schemaVersion:2",
            "deleteRecoverySession(moduleName,record)",
            "sessionId,fileName,dirty",
        ):
            self.assertIn(token, text)

        discard = text[text.index("async function discardCurrent()") : text.index("function updateFileName", text.index("async function discardCurrent()"))]
        self.assertIn("deleteSnapshotsOnly(moduleName,key,sessionId)", discard)
        self.assertNotIn("deleteDocument", discard)

    def test_snapshot_limit_is_per_document_session(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        prune = text[text.index("async function prune(") : text.index("function randomKey()")]
        self.assertIn("item.documentKey===documentKey&&sameSession(item,sessionId)", prune)
        self.assertIn("documentSnapshots.slice(MAX_PER_DOCUMENT)", prune)
        self.assertIn("groupCounts", prune)
        self.assertIn("(groupCounts.get(key)||0)>1", prune)

    def test_restore_rehomes_recovery_into_current_session(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        restore = text[text.index("restore:async()=>{") : text.index("function getState()")]
        self.assertIn("await deleteRecoverySession(moduleName,record)", restore)
        self.assertIn("await flush()", restore)
        self.assertNotIn("sessionId=record.sessionId", restore)

    def test_documents_discard_only_after_successful_replacement(self):
        text = (ROOT / "apps/documents/app.js").read_text(encoding="utf-8")
        open_block = text[text.index("async function openFile(file)") : text.index("async function createBlankDocument()")]
        parse_pos = open_block.index("parsed=await LocalDocxParser.parse(nextBuffer)")
        discard_pos = open_block.index("await recovery.discardCurrent()")
        start_pos = open_block.index("await recovery.startDocument")
        self.assertLess(parse_pos, discard_pos)
        self.assertLess(discard_pos, start_pos)
        self.assertNotIn("discardCurrent", open_block[:parse_pos])

        blank = text[text.index("async function createBlankDocument()") : text.index("function closeNewDocumentDialog()")]
        self.assertIn("await recovery.discardCurrent()", blank)
        self.assertIn("await recovery.startDocument", blank)

    def test_presentations_replace_recovery_transactionally(self):
        controller = (ROOT / "apps/presentations/io/recovery-controller.js").read_text(encoding="utf-8")
        for method in ("async startNewDocument()", "async startOpenedFile(file, buffer)"):
            self.assertIn(method, controller)
        self.assertGreaterEqual(controller.count("await this.manager.discardCurrent();"), 2)

        app = (ROOT / "apps/presentations/app.js").read_text(encoding="utf-8")
        choose = app[app.index("async function chooseTemplate(layout)") : app.index("function newPresentation()")]
        self.assertIn("await recoveryController.startNewDocument()", choose)

    def test_spreadsheet_new_document_awaits_recovery_transition(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        block = text[text.index("async function newWorkbook()") : text.index("function clearSelection()")]
        self.assertIn("await recovery.discardCurrent()", block)
        self.assertIn("await recovery.startDocument", block)

    def test_browser_recovery_suite_contains_multi_session_case(self):
        text = (ROOT / "tests/browser/revalidate_v0202_local_recovery.py").read_text(encoding="utf-8")
        for token in (
            "recovery_session_isolation_case",
            "recovery-session-isolation",
            "session-a",
            "session-b",
            "otherSessionPreserved",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
