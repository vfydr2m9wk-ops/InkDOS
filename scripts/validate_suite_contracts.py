from pathlib import Path
import hashlib,json,re,unittest
ROOT=Path(__file__).resolve().parents[1]
ACTIVE=('documents','spreadsheets','presentations','txt','epub','pdf')
class SuiteIntegration(unittest.TestCase):
    def test_home_routes(self):
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        for app in ACTIVE:
            self.assertIn(f'./apps/{app}/index.html?v=2.0.8',text)
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
        self.assertIn('./apps/presentations/index.html?v=2.0.8',home)

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
    def test_empty_state_file_action_contract(self):
        documents=(ROOT/'apps/documents/index.html').read_text(encoding='utf-8')
        self.assertRegex(documents,r'id="saveMenuBtn"[^>]*disabled')
        doc_save=(ROOT/'apps/documents/io/save-controller.js').read_text(encoding='utf-8')
        self.assertGreaterEqual(doc_save.count('if(!session.active)'),2)

        sheet_index=(ROOT/'apps/spreadsheets/index.html').read_text(encoding='utf-8')
        self.assertRegex(sheet_index,r'id="menuSave"[^>]*disabled')
        sheet_css=(ROOT/'apps/spreadsheets/runtime/frame/app-frame.css').read_text(encoding='utf-8')
        self.assertIn('.menu-item:disabled',sheet_css)
        sheets=(ROOT/'apps/spreadsheets/ui/chrome-controller.js').read_text(encoding='utf-8')
        self.assertIn("const active=!!session.book?.loaded",sheets)
        self.assertIn('if(save)save.disabled=!active',sheets)
        self.assertIn('if(share)share.disabled=!active',sheets)
        sheet_save=(ROOT/'apps/spreadsheets/io/save-controller.js').read_text(encoding='utf-8')
        self.assertGreaterEqual(sheet_save.count('if(!session.book?.loaded)return false'),2)

        presentation_session=(ROOT/'apps/presentations/engine/presentation-session.js').read_text(encoding='utf-8')
        self.assertIn("this.sourceKind='none'",presentation_session)
        self.assertIn('get active()',presentation_session)
        self.assertNotIn('this.compatibility=[];this.resetNew()',presentation_session)
        presentation_commands=(ROOT/'apps/presentations/ui/command-controller.js').read_text(encoding='utf-8')
        self.assertIn('const active=session.active',presentation_commands)
        self.assertIn("$('saveMenuBtn').disabled=!canExport",presentation_commands)
        self.assertIn('share.disabled=!canExport',presentation_commands)
        presentation_save=(ROOT/'apps/presentations/io/save-controller.js').read_text(encoding='utf-8')
        self.assertGreaterEqual(presentation_save.count('if(!session.active||busy)return null'),2)

        txt_editor=(ROOT/'apps/txt/editor/editor-controller.js').read_text(encoding='utf-8')
        self.assertIn('E.saveBtn.disabled=!state.loaded;E.shareBtn.disabled=!state.loaded',txt_editor)
        txt_files=(ROOT/'apps/txt/io/txt-file-controller.js').read_text(encoding='utf-8')
        self.assertIn('function initializeEmptyState()',txt_files)
        self.assertIn('function initialize(){initializeEmptyState();restoreRecovery()}',txt_files)
        self.assertGreaterEqual(txt_files.count('if(!state.loaded)return'),2)

        epub=(ROOT/'apps/epub/index.html').read_text(encoding='utf-8')
        self.assertRegex(epub,r'id="saveBtn"[^>]*disabled')
        self.assertRegex(epub,r'id="shareBtn"[^>]*disabled')

        pdf_index=(ROOT/'apps/pdf/index.html').read_text(encoding='utf-8')
        self.assertRegex(pdf_index,r'id="saveMenuBtn"[^>]*disabled')
        self.assertRegex(pdf_index,r'id="saveToolbarBtn"[^>]*disabled')
        pdf_css=(ROOT/'apps/pdf/runtime/frame/app-frame.css').read_text(encoding='utf-8')
        self.assertIn('.menu-item:disabled',pdf_css)
        pdf=(ROOT/'apps/pdf/ui/command-controller.js').read_text(encoding='utf-8')
        self.assertIn("$('saveMenuBtn').disabled=!active",pdf)
        self.assertIn("$('saveToolbarBtn').disabled=!active",pdf)
        self.assertIn('share.disabled=!active',pdf)
        pdf_save=(ROOT/'apps/pdf/io/save-controller.js').read_text(encoding='utf-8')
        self.assertGreaterEqual(pdf_save.count('if(!session.active||saving)return null'),2)
    def test_mobile_home_layout(self):
        css=(ROOT/'assets/home.css').read_text(encoding='utf-8')
        self.assertIn('@media(max-width:720px)',css);self.assertIn('.workspace-grid{grid-template-columns:1fr',css)
    def test_no_cross_suite_runtime_roots(self):
        for rel in ('shared','modules','core'):self.assertFalse((ROOT/rel).exists(),rel)
    def test_source_lock_has_six_apps(self):
        lock=json.loads((ROOT/'SOURCE_LOCK.json').read_text(encoding='utf-8'))
        self.assertEqual(set(lock['apps']),set(ACTIVE))
if __name__=='__main__':unittest.main()
