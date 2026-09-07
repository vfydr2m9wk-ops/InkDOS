from pathlib import Path
import hashlib,json,re,unittest
ROOT=Path(__file__).resolve().parents[1]
ACTIVE=('documents','spreadsheets','presentations','txt','epub')
class SuiteIntegration(unittest.TestCase):
    def test_home_routes(self):
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        for app in ACTIVE:self.assertIn(f'./apps/{app}/index.html',text)
    def test_standard_start_cards(self):
        two_action=('documents','spreadsheets','presentations','txt')
        for app in two_action:
            text=(ROOT/f'apps/{app}/index.html').read_text(encoding='utf-8')
            self.assertIn('start-card',text,app);self.assertIn('id="startNew"',text,app);self.assertIn('id="startOpen"',text,app)
        epub=(ROOT/'apps/epub/index.html').read_text(encoding='utf-8')
        self.assertIn('start-card',epub);self.assertIn('id="openStartBtn"',epub);self.assertNotIn('id="startNew"',epub)
    def test_pdf_placeholder(self):
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('PDF Workspace',text);self.assertIn('Coming soon',text);self.assertFalse((ROOT/'apps/pdf').exists())
    def test_return_bridge(self):
        for app in ACTIVE:
            text=(ROOT/f'apps/{app}/index.html').read_text(encoding='utf-8')
            self.assertIn('../../index.html',text);self.assertIn('aria-label="Home"',text)
    def test_mobile_home_layout(self):
        css=(ROOT/'assets/home.css').read_text(encoding='utf-8')
        self.assertIn('@media(max-width:720px)',css);self.assertIn('.workspace-grid{grid-template-columns:1fr',css)
    def test_no_cross_suite_runtime_roots(self):
        for rel in ('shared','modules','core','apps/pdf'):self.assertFalse((ROOT/rel).exists(),rel)
    def test_source_lock_has_five_apps(self):
        lock=json.loads((ROOT/'SOURCE_LOCK.json').read_text(encoding='utf-8'))
        self.assertEqual(set(lock['apps']),set(ACTIVE))
if __name__=='__main__':unittest.main()
