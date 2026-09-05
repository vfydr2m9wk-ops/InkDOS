from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ResponsivePdfReflowTests(unittest.TestCase):
    def test_pdf_responsive_styles_are_loaded(self):
        html = (ROOT / "apps/pdf/index.html").read_text(encoding="utf-8")
        self.assertIn("responsive-reflow.css", html)
        self.assertIn("viewer/responsive-controller.js", html)

    def test_pdf_responsive_css_reflows_chrome(self):
        css = (ROOT / "apps/pdf/responsive-reflow.css").read_text(encoding="utf-8")
        self.assertIn("flex-wrap:wrap!important", css)
        self.assertIn("grid-template-columns:minmax(0,1fr)!important", css)
        self.assertIn("grid-template-rows:44px auto minmax(0,1fr) 44px!important", css)
        self.assertIn(".pdf-page-shell", css)
        self.assertIn("@media (max-width:420px)", css)

    def test_pdf_renderer_uses_live_container_padding(self):
        renderer = (ROOT / "apps/pdf/viewer/page-renderer.js").read_text(encoding="utf-8")
        self.assertIn("getComputedStyle(E.pdfPages)", renderer)
        self.assertIn("horizontalPadding", renderer)
        self.assertIn("const availableWidth = Math.max(", renderer)
        self.assertIn("E.viewerStage.clientWidth - horizontalPadding", renderer)
        self.assertIn("const availableHeight = Math.max(", renderer)
        self.assertIn("E.viewerStage.clientHeight - verticalPadding", renderer)

    def test_pdf_viewer_observes_resizes_in_modular_controller(self):
        app = (ROOT / "apps/pdf/app.js").read_text(encoding="utf-8")
        controller = (ROOT / "apps/pdf/viewer/responsive-controller.js").read_text(encoding="utf-8")
        self.assertLessEqual(len(app.splitlines()), 500)
        self.assertIn("new ResizeObserver", controller)
        self.assertIn("page-width", controller)
        self.assertIn("page-fit", controller)
        self.assertIn("observer?.observe(stage)", controller)
        self.assertIn("InkDOSPdfDebug", controller)

if __name__ == "__main__":
    unittest.main()
