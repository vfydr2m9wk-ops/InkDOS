from pathlib import Path
import hashlib,json,re,unittest
ROOT=Path(__file__).resolve().parents[1]
ACTIVE=('documents','spreadsheets','presentations','txt','epub','pdf')
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
    def test_presentations_start_gate_is_behavioral(self):
        text=(ROOT/'apps/presentations/index.html').read_text(encoding='utf-8')
        self.assertIn('presentationStartGate',text)
        self.assertIn('showStart()',text)
        self.assertIn('waitForOpenCommit',text)
        self.assertIn('app.newPresentation()',text)
        self.assertIn('display:grid!important',text)
        self.assertIn('.start-state[hidden]{display:none!important}',text)
        home=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('./apps/presentations/index.html?v=2.0.2',home)

    def test_pdf_active(self):
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('PDF Workspace',text);self.assertNotIn('Coming soon',text);self.assertTrue((ROOT/'apps/pdf/index.html').is_file())
    def test_return_bridge(self):
        for app in ACTIVE:
            text=(ROOT/f'apps/{app}/index.html').read_text(encoding='utf-8')
            self.assertIn('../../index.html',text);self.assertIn('aria-label="Home"',text)
    def test_share_action_contract(self):
        direct={'txt':('index.html','shareBtn'),'epub':('index.html','shareBtn')}
        runtime={
            'documents':('ui/command-controller.js','shareMenuBtn'),
            'spreadsheets':('ui/file-menu-controller.js','menuShare'),
            'presentations':('ui/command-controller.js','shareMenuBtn'),
            'pdf':('ui/command-controller.js','shareMenuBtn'),
        }
        for app,(rel,marker) in {**direct,**runtime}.items():
            text=(ROOT/'apps'/app/rel).read_text(encoding='utf-8')
            self.assertIn(marker,text,app);self.assertIn('Share',text,app)
        for app in runtime:
            delivery=(ROOT/'apps'/app/'io/file-delivery.js').read_text(encoding='utf-8')
            self.assertIn('share',delivery,app)
    def test_mobile_home_layout(self):
        css=(ROOT/'assets/home.css').read_text(encoding='utf-8')
        self.assertIn('@media(max-width:720px)',css);self.assertIn('.workspace-grid{grid-template-columns:1fr',css)
    def test_no_cross_suite_runtime_roots(self):
        for rel in ('shared','modules','core'):self.assertFalse((ROOT/rel).exists(),rel)
    def test_source_lock_has_six_apps(self):
        lock=json.loads((ROOT/'SOURCE_LOCK.json').read_text(encoding='utf-8'))
        self.assertEqual(set(lock['apps']),set(ACTIVE))
if __name__=='__main__':unittest.main()
