from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RecoveryPromptStartupSafetyTests(unittest.TestCase):
    def test_shared_recovery_invalidates_stale_async_prompt(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        block = text[text.index("async function promptLatest()") : text.index("function getState()")]
        self.assertIn("const token=++promptEpoch", block)
        self.assertIn("capturedGeneration=generation", block)
        self.assertIn("capturedDocumentKey=documentKey", block)
        self.assertIn("token===promptEpoch", block)
        self.assertIn("capturedGeneration===generation", block)
        self.assertIn("capturedDocumentKey===documentKey", block)
        self.assertGreaterEqual(block.count("stillCurrent()"), 2)

    def test_shared_recovery_exposes_explicit_prompt_cancellation(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        self.assertIn("function cancelPrompt()", text)
        self.assertIn("activePrompt.remove()", text)
        self.assertIn("updateFileName,cancelPrompt,promptLatest", text)

    def test_documents_cancel_prompt_before_slow_replacement_parse(self):
        text = (ROOT / "apps/documents/app.js").read_text(encoding="utf-8")
        block = text[text.index("async function openFile(file)") : text.index("async function createBlankDocument()")]
        self.assertLess(block.index("recovery.cancelPrompt()"), block.index("file.arrayBuffer()"))
        blank = text[text.index("async function createBlankDocument()") : text.index("function closeNewDocumentDialog()")]
        self.assertLess(blank.index("recovery.cancelPrompt()"), blank.index("recovery.discardCurrent()"))

    def test_spreadsheets_cancel_prompt_before_open_and_new_transition(self):
        text = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        open_block = text[text.index("async function openFile(file)") : text.index("async function prepareSave()")]
        self.assertLess(open_block.index("recovery.cancelPrompt()"), open_block.index("file.arrayBuffer()"))
        new_block = text[text.index("async function newWorkbook()") : text.index("function clearSelection()")]
        self.assertLess(new_block.index("recovery.cancelPrompt()"), new_block.index("recovery.discardCurrent()"))

    def test_presentations_cancel_prompt_when_file_is_selected(self):
        app = (ROOT / "apps/presentations/app.js").read_text(encoding="utf-8")
        wrapper = app[app.index("async function loadPptx(file)") : app.index("function cleanPptText")]
        self.assertLess(wrapper.index("recoveryController.cancelPrompt()"), wrapper.index("fileController.load(file)"))
        controller = (ROOT / "apps/presentations/io/recovery-controller.js").read_text(encoding="utf-8")
        self.assertIn("cancelPrompt()", controller)
        self.assertGreaterEqual(controller.count("this.manager.cancelPrompt();"), 3)

    def test_browser_recovery_suite_reproduces_startup_prompt_race(self):
        text = (ROOT / "tests/browser/revalidate_v0202_local_recovery.py").read_text(encoding="utf-8")
        self.assertIn("def recovery_prompt_startup_race_case", text)
        self.assertIn("const pendingPrompt = manager.promptLatest();", text)
        self.assertIn("await manager.startDocument({documentKey:'current-doc'", text)
        self.assertIn("manager.cancelPrompt();", text)
        self.assertIn('"recovery-prompt-startup-race"', text)


if __name__ == "__main__":
    unittest.main()
