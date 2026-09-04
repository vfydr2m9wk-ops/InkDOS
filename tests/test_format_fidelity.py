from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FormatFidelityCorrection02031Tests(unittest.TestCase):
    def test_documents_loads_drawing_layout_before_parser(self):
        html = (ROOT / 'apps/documents/index.html').read_text(encoding='utf-8')
        self.assertIn('drawing-layout.js?v=1.0.0-beta.5', html)
        self.assertLess(html.index('drawing-layout.js?v=1.0.0-beta.5'), html.index('docx-parser.js?v=1.0.0-beta.5'))

    def test_docx_parser_preserves_drawing_geometry_anchor_and_header_artwork(self):
        parser = (ROOT / 'apps/documents/docx-parser.js').read_text(encoding='utf-8')
        helper = (ROOT / 'apps/documents/drawing-layout.js').read_text(encoding='utf-8')
        app = (ROOT / 'apps/documents/app.js').read_text(encoding='utf-8')
        self.assertIn('InkDOSDocumentDrawingLayout.imageLayout(drawing', parser)
        self.assertIn('vmlImageLayout(shape)', helper)
        self.assertIn('headerArtwork:header.artwork', parser)
        self.assertIn('EMU_PER_CSS_PIXEL=9525', helper)
        self.assertIn("horizontal.relativeFrom==='column'", helper)
        self.assertIn('horizontal.offsetPx-paragraphLeftPx', helper)
        self.assertIn('appendPageArtwork(page,spec)', app)
        self.assertIn('.page-watermark{position:absolute', helper)
        self.assertIn('.page .has-docx-anchor{position:relative', helper)
        self.assertIn("font-family:'", parser)
        self.assertNotIn("font-family:'+JSON.stringify(props.fontFamily)", parser)

    def test_presentations_loads_background_resolver_before_app(self):
        html = (ROOT / 'apps/presentations/index.html').read_text(encoding='utf-8')
        self.assertIn('engine/background-resolver.js?v=1.0.0-beta.5', html)
        self.assertLess(html.index('engine/background-resolver.js?v=1.0.0-beta.5'), html.index('app.js?v=1.0.0-beta.5'))

    def test_presentations_resolves_direct_background_images_without_expanding_main_app(self):
        app = (ROOT / 'apps/presentations/app.js').read_text(encoding='utf-8')
        helper = (ROOT / 'apps/presentations/engine/background-resolver.js').read_text(encoding='utf-8')
        self.assertIn('InkDOSPresentationsBackground.resolve', app)
        self.assertIn("first(bg,'blipFill')", helper)
        self.assertIn("size:'100% 100%'", helper)
        self.assertLessEqual(len(app.splitlines()), 698)

    def test_new_runtime_modules_are_offline_cached(self):
        worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        self.assertIn('./apps/documents/drawing-layout.js', worker)
        self.assertIn('./apps/presentations/engine/background-resolver.js', worker)


if __name__ == '__main__':
    unittest.main()
