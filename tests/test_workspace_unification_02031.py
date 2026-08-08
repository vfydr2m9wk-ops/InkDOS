from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "shared" / "ui" / "workspace-unification-v02031.css"


class WorkspaceUnification02031Tests(unittest.TestCase):
    def test_overlay_is_loaded_last_and_launcher_is_excluded(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 420)
        self.assertIn("Documents is the visual shell reference", text)
        self.assertNotIn("workspace-card", text)
        self.assertNotIn("hub-shell", text)
        shell = (ROOT / "shared" / "office-shell.js").read_text(encoding="utf-8")
        content = shell.index("addStylesheet('content-workspaces-v02031.css')")
        unified = shell.index("addStylesheet('workspace-unification-v02031.css')")
        self.assertLess(content, unified)

    def test_service_worker_precaches_unification_layer(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("./shared/ui/workspace-unification-v02031.css", worker)

    def test_documents_style_shell_is_applied_across_workspaces(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("--ink-workspace-titlebar:44px", text)
        self.assertIn("--ink-workspace-statusbar:34px", text)
        for klass in (
            "office-spreadsheets", "office-presentations", "office-pdf",
            "office-txt", "office-epub",
        ):
            self.assertIn(f"body.{klass}", text)
        self.assertIn("body.office-pdf .commandbar", text)
        self.assertIn("justify-content:center!important", text)

    def test_bottom_zoom_contract_is_present_in_every_workspace(self):
        documents = (ROOT / "apps/documents/index.html").read_text(encoding="utf-8")
        sheets = (ROOT / "apps/spreadsheets/index.html").read_text(encoding="utf-8")
        slides = (ROOT / "apps/presentations/index.html").read_text(encoding="utf-8")
        pdf = (ROOT / "apps/pdf/index.html").read_text(encoding="utf-8")
        txt = (ROOT / "apps/txt/index.html").read_text(encoding="utf-8")
        epub = (ROOT / "apps/epub/index.html").read_text(encoding="utf-8")
        for html, slider, fit in (
            (documents, 'id="zoomSlider"', 'id="fitWidth"'),
            (sheets, 'id="zoomSlider"', 'id="fitWidth"'),
            (slides, 'id="bottomZoomRange"', 'id="bottomFitBtn"'),
            (pdf, 'id="pdfZoomSlider"', 'id="pdfFitWidth"'),
            (txt, 'id="txtZoomSlider"', 'id="txtFit"'),
            (epub, 'id="epubZoomSlider"', 'id="epubFit"'),
        ):
            self.assertIn(slider, html)
            self.assertIn(fit, html)

    def test_pdf_and_presentations_sidebars_push_content(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:var(--slides-w) minmax(0,1fr) var(--inspector-w)!important", text)
        self.assertIn("body.office-pdf .workspace-body", text)
        self.assertIn("grid-template-columns:220px minmax(0,1fr)!important", text)
        self.assertIn("body.office-pdf .sidebar", text)
        self.assertIn("position:relative!important", text)

    def test_epub_theme_controls_are_small_integrated_circles(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("body.office-epub .theme-controls", text)
        self.assertIn("border:0!important", text)
        self.assertIn("body.office-epub .theme-dot{", text)
        self.assertIn("width:18px!important", text)
        self.assertIn("border-radius:999px!important", text)

    def test_editors_are_ipad_landscape_baseline_and_wide_expanding(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("@media(min-width:1180px)", text)
        self.assertIn("@media(min-width:1700px)", text)
        self.assertIn("min-width:820px!important", text)
        self.assertIn("display:inline-grid!important", text)

    def test_shell_fidelity_pass_keeps_documents_geometry_and_wide_rules(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("UI shell fidelity pass 5", text)
        self.assertIn("grid-template-columns:minmax(0,1fr) auto minmax(0,1fr)!important", text)
        self.assertIn("body.office-spreadsheets .viewer-label{display:none!important}", text)
        self.assertIn("body.office-presentations .present-top-action span{display:none!important}", text)
        self.assertIn("--ink-workspace-sidebar:238px", text)
        self.assertIn("body.office-documents .sidebar{width:238px!important}", text)
        self.assertNotIn("body.office-documents .workspace{grid-template-columns:250px minmax(0,1fr)!important}", text)
        self.assertIn("body.office-presentations .workspace{--slides-w:188px!important}", text)
        self.assertIn("body.office-pdf .workspace-body{grid-template-columns:220px minmax(0,1fr)!important}", text)
        self.assertNotIn("--slides-w:210px", text)
        self.assertNotIn("grid-template-columns:244px minmax(0,1fr)", text)
        self.assertIn("body.office-documents .viewport{padding-inline:clamp(28px,2vw,42px)!important}", text)

    def test_overlay_contains_no_data_or_storage_logic(self):
        text = CSS.read_text(encoding="utf-8").lower()
        for forbidden in ("indexeddb", "localstorage", "formulaengine", "undostack", "fetch("):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
