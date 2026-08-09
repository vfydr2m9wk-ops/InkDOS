import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StabilityCorrectionsCandidateTests(unittest.TestCase):
    def test_light_only_policy_and_future_dark_gate(self):
        shell=(ROOT/'shared/office-shell.js').read_text()
        self.assertIn("addStylesheet('light-only.css');",shell)
        self.assertGreater(shell.index("addStylesheet('light-only.css');"),shell.index("addStylesheet('spreadsheets-beta1-polish.css');"))
        light=(ROOT/'shared/ui/light-only.css').read_text()
        self.assertIn('color-scheme: light !important',light)
        self.assertIn('body.office-spreadsheets',light)
        self.assertTrue((ROOT/'shared/future/dark-theme.css').is_file())
        self.assertNotIn('shared/future/dark-theme.css',(ROOT/'service-worker.js').read_text())

    def test_pdf_render_window_is_retired_only_after_incoming_render(self):
        renderer=(ROOT/'apps/pdf/viewer/page-renderer.js').read_text()
        self.assertIn('const CACHE_RADIUS = 2',renderer)
        render_call="await Promise.all(\n        [...wanted].map(pageNumber => renderPage(pageNumber))\n      );"
        self.assertIn(render_call,renderer)
        self.assertGreater(renderer.index('for (const [pageNumber, record] of [...state.rendered])',renderer.index(render_call)),renderer.index(render_call))
        self.assertIn('state.rendered.get(pageNumber)?.task !== task',renderer)
        self.assertIn('viewportRelevant(pageNumber)',renderer)

    def test_pdf_fullscreen_does_not_rebuild_renderer(self):
        controller=(ROOT/'apps/pdf/viewer/fullscreen-controller.js').read_text()
        self.assertIn("document.addEventListener('fullscreenchange'",controller)
        self.assertNotIn('requestAnimationFrame(() => requestAnimationFrame(() => {',controller)
        self.assertNotIn('rerender();',controller)
        self.assertNotIn('fitWidth(',controller)
        self.assertNotIn('requestFullscreen()',controller)

    def test_presentation_hidden_format_panel_does_not_reserve_track(self):
        css=(ROOT/'apps/presentations/stability.css').read_text()
        html=(ROOT/'apps/presentations/index.html').read_text()
        self.assertIn('grid-template-columns:var(--slides-w) minmax(0,1fr) !important',css)
        self.assertIn('display:none !important',css)
        self.assertIn('stability.css?v=stability-1',html)

    def test_presentation_common_edits_are_undoable(self):
        app=(ROOT/'apps/presentations/app.js').read_text()
        for marker in [
            "$('dupSlideBtn').onclick=()=>historyController.action",
            "$('insertTextBtn').onclick=()=>historyController.action",
            "$('insertShapeBtn').onclick=()=>historyController.action",
            "rd.onload=()=>historyController.action",
            "$('frontBtn').onclick=()=>{const o=obj();if(o)historyController.action",
            "$('backBtn').onclick=()=>{const o=obj();if(o)historyController.action",
            "function applyText(fn){const o=obj();if(o&&o.type==='text')historyController.action",
        ]:
            self.assertIn(marker,app)


    def test_light_only_has_no_active_dark_media(self):
        runtime_css = [p for p in ROOT.rglob('*.css') if 'shared/future' not in p.as_posix()]
        offenders=[]
        for path in runtime_css:
            text=path.read_text()
            if 'prefers-color-scheme:dark' in text.replace(' ','') or 'prefers-color-scheme: dark' in text:
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])
        self.assertIn("inkdesk-shell-v1.0.0-beta.1-pdf53", (ROOT/'service-worker.js').read_text())

    def test_presentation_pointer_edits_are_undoable(self):
        selection=(ROOT/'apps/presentations/state/selection-controller.js').read_text()
        app=(ROOT/'apps/presentations/app.js').read_text()
        self.assertIn('before: this.captureHistory()', selection)
        self.assertIn('this.pushHistory(drag.before)', selection)
        self.assertIn('captureHistory:()=>historyController?historyController.capture():null', app)
        self.assertIn("event.metaKey||event.ctrlKey", app)


    def test_pdf_fullscreen_is_universal_non_destructive_content_focus(self):
        app=(ROOT/'apps/pdf/app.js').read_text()
        html=(ROOT/'apps/pdf/index.html').read_text()
        controller=(ROOT/'apps/pdf/viewer/fullscreen-controller.js').read_text()
        css=(ROOT/'apps/pdf/fullscreen-mobile.css').read_text()
        worker=(ROOT/'service-worker.js').read_text()
        self.assertIn('InkDeskPdfFullscreen.create', app)
        self.assertIn("classList.toggle('immersive', enabled)", controller)
        self.assertIn("classList.toggle('pdf-fullscreen', enabled)", controller)
        self.assertIn("classList.toggle('content-focus-mode', enabled)", controller)
        self.assertNotIn('requestFullscreen()', controller)
        self.assertNotIn('fitWidth(12)', controller)
        self.assertNotIn("matchMedia('(orientation: portrait)').matches", controller)
        self.assertIn('body.pdf-fullscreen .commandbar', css)
        self.assertIn('body.content-focus-mode .commandbar', css)
        self.assertNotIn('@media(max-width:650px)', css)
        self.assertIn('height:100dvh', css)
        self.assertIn('fullscreen-mobile.css?v=1.0.0-beta.1-pdf53', html)
        self.assertIn('viewer/fullscreen-controller.js?v=1.0.0-beta.1-pdf53', html)
        self.assertIn("'./apps/pdf/fullscreen-mobile.css'", worker)
        self.assertIn("'./apps/pdf/viewer/fullscreen-controller.js'", worker)

    def test_documents_toolbar_contract(self):
        html=(ROOT/'apps/documents/index.html').read_text()
        app=(ROOT/'apps/documents/app.js').read_text()
        self.assertIn('id="alignmentSelect"',html)
        self.assertIn('data-cmd="outdent"',html)
        self.assertIn('data-cmd="indent"',html)
        self.assertNotIn('>• List<',html)
        self.assertNotIn('>1. List<',html)
        self.assertNotIn('>A. List<',html)
        self.assertNotIn('>Row +<',html)
        self.assertNotIn('>Col +<',html)
        self.assertNotIn('>Image<',html)
        self.assertIn("$('alignmentSelect').onchange",app)

    def test_file_router_validates_message_origin(self):
        router=(ROOT/'shared/file-router.js').read_text()
        self.assertIn('function trustedMessage(event,source)',router)
        self.assertIn("event.origin===origin",router)
        self.assertIn("event.origin==='null'",router)
        self.assertNotIn("postMessage({type:'inkdesk:open-file',token,file},'*')",router)
        self.assertNotIn("postMessage({type:'inkdesk:workspace-ready',token:bridgeToken},'*')",router)

if __name__=='__main__':
    unittest.main()
