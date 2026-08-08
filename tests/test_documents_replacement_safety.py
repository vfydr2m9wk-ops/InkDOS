from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentsReplacementSafetyTests(unittest.TestCase):
    def test_open_guard_is_owned_by_documents_runtime(self):
        text = (ROOT / "apps/documents/app.js").read_text(encoding="utf-8")
        block = text[text.index("async function openFile(file)"):text.index("function createBlankDocument()")]
        self.assertIn("if(dirty&&!confirm(", block)
        self.assertIn("discard them only if the new document opens successfully", block)
        self.assertIn("Open canceled; unsaved document preserved", block)
        self.assertLess(block.index("if(dirty&&!confirm("), block.index("const previous="))
        self.assertLess(block.index("const previous="), block.index("setLoading('Opening "))

    def test_failed_open_still_rolls_back_after_user_accepts_replacement(self):
        text = (ROOT / "apps/documents/app.js").read_text(encoding="utf-8")
        block = text[text.index("async function openFile(file)"):text.index("function createBlankDocument()")]
        for marker in (
            "const previous={",
            "currentFile=previous.currentFile",
            "currentBuffer=previous.currentBuffer",
            "sourceContext=previous.sourceContext",
            "dirty=previous.dirty",
            "pagesHost.innerHTML=previous.content",
            "status('Open failed; previous document preserved')",
        ):
            self.assertIn(marker, block)

    def test_browser_regression_covers_cancel_and_failed_replacement(self):
        text = (ROOT / "tests/browser/revalidate_transactional_open_failures.py").read_text(encoding="utf-8")
        for marker in (
            "UNSAVED-DOCX-REPLACEMENT-GUARD",
            "replacement was canceled",
            "replacement did not warn about unsaved changes",
            "confirmed replacement failed to open",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
