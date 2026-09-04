import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StabilityContractTests(unittest.TestCase):
    def test_pdf_render_window_retires_only_after_incoming_render(self):
        renderer = (ROOT/'apps/pdf/viewer/page-renderer.js').read_text()
        render_call = "await Promise.all(\n        [...wanted].map(pageNumber => renderPage(pageNumber))\n      );"
        self.assertIn('const CACHE_RADIUS = 2', renderer)
        self.assertIn(render_call, renderer)
        self.assertGreater(renderer.index('for (const [pageNumber, record] of [...state.rendered])', renderer.index(render_call)), renderer.index(render_call))
        self.assertIn('viewportRelevant(pageNumber)', renderer)

    def test_pdf_fullscreen_is_non_destructive_content_focus(self):
        controller = (ROOT/'apps/pdf/viewer/fullscreen-controller.js').read_text()
        css = (ROOT/'apps/pdf/fullscreen-mobile.css').read_text()
        self.assertNotIn('requestFullscreen()', controller)
        self.assertIn("classList.toggle('content-focus-mode', enabled)", controller)
        self.assertIn('height:100dvh', css)

    def test_presentation_hidden_format_panel_does_not_reserve_track(self):
        css = (ROOT/'apps/presentations/stability.css').read_text()
        self.assertIn('grid-template-columns:var(--slides-w) minmax(0,1fr) !important', css)
        self.assertIn('display:none !important', css)

    def test_presentation_edits_remain_undoable(self):
        app = (ROOT/'apps/presentations/app.js').read_text()
        selection = (ROOT/'apps/presentations/state/selection-controller.js').read_text()
        self.assertIn("$('dupSlideBtn').onclick=()=>historyController.action", app)
        self.assertIn("$('insertTextBtn').onclick=()=>historyController.action", app)
        self.assertIn('before: this.captureHistory()', selection)
        self.assertIn('this.pushHistory(drag.before)', selection)

    def test_documents_toolbar_contract(self):
        html = (ROOT/'apps/documents/index.html').read_text()
        app = (ROOT/'apps/documents/app.js').read_text()
        self.assertIn('id="alignmentSelect"', html)
        self.assertIn('data-cmd="outdent"', html)
        self.assertIn('data-cmd="indent"', html)
        self.assertIn("$('alignmentSelect').onchange", app)

    def test_file_router_validates_message_origin(self):
        router = (ROOT/'shared/file-router.js').read_text()
        self.assertIn('function trustedMessage(event,source)', router)
        self.assertIn('event.origin===origin', router)
        self.assertIn("event.origin==='null'", router)
        self.assertNotIn("postMessage({type:'inkdos:open-file',token,file},'*')", router)


if __name__ == '__main__':
    unittest.main()
