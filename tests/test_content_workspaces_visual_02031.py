from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "shared" / "ui" / "content-workspaces-v02031.css"


class ContentWorkspacesVisual02031Tests(unittest.TestCase):
    def test_visual_layer_exists_is_bounded_and_presentation_only(self):
        text = CSS.read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertLessEqual(len(text.splitlines()), 500)
        for klass in ("office-documents", "office-txt", "office-epub"):
            self.assertIn(f"body.{klass}", text)
        for forbidden in (
            "indexeddb", "localstorage", "fetch(", "xmlhttprequest",
            "undostack", "formulaengine", "documentkey", "sessionid",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_layer_loads_after_shared_visual_foundation(self):
        shell = (ROOT / "shared" / "office-shell.js").read_text(encoding="utf-8")
        foundation = shell.index("addStylesheet('visual-foundation-v0203.css')")
        content = shell.index("addStylesheet('content-workspaces-v02031.css')")
        self.assertLess(foundation, content)

    def test_service_worker_precaches_content_visual_layer(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("./shared/ui/content-workspaces-v02031.css", worker)

    def test_documents_refinement_keeps_document_controls_visible(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("body.office-documents .formatbar", text)
        self.assertIn("body.office-documents .workspace", text)
        self.assertIn("body.office-documents .page", text)
        self.assertIn("body.office-documents #saveBtn:not(:disabled)", text)
        for control in ("#newBtn", "#undoBtn", "#redoBtn", "#sidebarBtn", "#saveBtn"):
            self.assertNotIn(f"{control}{{display:none", text.replace(" ", ""))

    def test_txt_and_epub_receive_distinct_reading_writing_surfaces(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("body.office-txt .editor-shell", text)
        self.assertIn("body.office-txt #editor", text)
        self.assertIn("body.office-epub .page-surface", text)
        self.assertIn("body.office-epub .page-content", text)
        self.assertIn("body.office-epub .toc-panel", text)

    def test_narrow_and_coarse_pointer_refinements_exist(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("@media(max-width:760px)", text)
        self.assertIn("@media(max-width:520px)", text)
        self.assertIn("@media(pointer:coarse)", text)
        self.assertIn("body.office-epub .reader-toolbar{min-height:36px!important;height:36px!important", text)
        self.assertIn("body.office-txt .txt-statusbar,body.office-epub .reader-statusbar{min-height:34px!important;height:34px!important", text)
        self.assertIn("@media(prefers-reduced-motion:reduce)", text)


if __name__ == "__main__":
    unittest.main()
