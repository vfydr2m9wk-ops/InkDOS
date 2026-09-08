from pathlib import Path
import hashlib,json,re,unittest
ROOT=Path(__file__).resolve().parents[1]
ACTIVE=('documents','spreadsheets','presentations','txt','epub','pdf')
class SuiteIntegration(unittest.TestCase):
    def test_home_routes(self):
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        for app in ACTIVE:
            self.assertIn(f'./apps/{app}/index.html?v=2.0.12&amp;suite=1',text)
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
        self.assertIn('./apps/presentations/index.html?v=2.0.12&amp;suite=1',home)

    def test_pdf_active(self):
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('PDF Workspace',text);self.assertNotIn('Coming soon',text);self.assertTrue((ROOT/'apps/pdf/index.html').is_file())
    def test_pdf_frame_visual_contract(self):
        self.assertEqual((ROOT/'apps/pdf/assets/pdf.svg').read_bytes(),(ROOT/'assets/icons/pdf.svg').read_bytes())
        css=(ROOT/'apps/pdf/runtime/frame/app-frame.css').read_text(encoding='utf-8')
        self.assertIn('.document-title{position:absolute;left:50%',css)
        self.assertIn('.title-text{height:100%',css)
        self.assertIn('border:1px solid var(--line)',css)
        self.assertIn('.pdf-icon{width:30px',css)
        controller=(ROOT/'apps/pdf/ui/chrome-controller.js').read_text(encoding='utf-8')
        self.assertIn("const title=$('titleText')",controller)
        self.assertIn("session.fileName:'No PDF open'",controller)
    def test_return_bridge(self):
        for app in ACTIVE:
            text=(ROOT/f'apps/{app}/index.html').read_text(encoding='utf-8')
            self.assertIn('../../index.html',text);self.assertIn('aria-label="Home"',text)
    def test_horizontal_appearance_contract(self):
        home=(ROOT/'index.html').read_text(encoding='utf-8')
        css=(ROOT/'assets/home.css').read_text(encoding='utf-8')
        self.assertIn('inkdos2:appearance',home)
        self.assertIn('id="appearanceButton"',home);self.assertIn('id="appearanceMenu"',home)
        for mode in ('light','dark','system'): self.assertIn(f'data-home-appearance-mode="{mode}"',home)
        self.assertIn('html[data-theme="dark"]',css)
        local_keys={
            'documents':'inkdos2:documents:appearance','spreadsheets':'inkdos2:spreadsheets:appearance','presentations':'inkdos2:presentations:appearance',
            'txt':'inkdos2:txt:appearance','epub':'inkdos2:epub:appearance','pdf':'inkdos2:pdf:p1:appearance'}
        for app,local_key in local_keys.items():
            text=(ROOT/'apps'/app/'state'/'appearance.js').read_text(encoding='utf-8')
            self.assertIn(local_key,text,app);self.assertIn('inkdos2:appearance',text,app);self.assertIn("'storage'",text,app)
    def test_share_action_contract(self):
        direct={'txt':('index.html','shareBtn'),'epub':('index.html','shareBtn')}
        runtime={
            'documents':('ui/command-controller.js','shareMenuBtn'),
            'spreadsheets':('ui/file-menu-controller.js','menuShare'),
            'presentations':('ui/command-controller.js','shareMenuBtn'),
        }
        for app,(rel,marker) in {**direct,**runtime}.items():
            text=(ROOT/'apps'/app/rel).read_text(encoding='utf-8')
            self.assertIn(marker,text,app);self.assertIn('Share',text,app)
        pdf_bindings=(ROOT/'apps/pdf/ui/command-bindings.js').read_text(encoding='utf-8')
        pdf_commands=(ROOT/'apps/pdf/ui/command-controller.js').read_text(encoding='utf-8')
        self.assertIn("share.id='shareMenuBtn'",pdf_bindings)
        self.assertIn("share.dataset.command='file.share'",pdf_bindings)
        self.assertIn("registry.bindElement(share,'file.share')",pdf_bindings)
        self.assertIn("registry.register('file.share'",pdf_commands)
        self.assertIn('Share',pdf_bindings)
        for app in (*runtime,'pdf'):
            delivery=(ROOT/'apps'/app/'io/file-delivery.js').read_text(encoding='utf-8')
            self.assertIn('share',delivery,app)
    def test_single_save_delivery_contract(self):
        files={
            'documents':ROOT/'apps/documents/io/file-delivery.js',
            'spreadsheets':ROOT/'apps/spreadsheets/io/file-delivery.js',
            'presentations':ROOT/'apps/presentations/io/file-delivery.js',
            'txt':ROOT/'apps/txt/runtime/services/file-delivery.js',
            'pdf':ROOT/'apps/pdf/io/file-delivery.js',
        }
        texts={app:path.read_text(encoding='utf-8') for app,path in files.items()}
        for app,text in texts.items():
            self.assertIn('isAppleTouchHost',text,app)
            self.assertIn('write-failed',text,app)
        for app in ('documents','spreadsheets','presentations','txt'):
            self.assertIn("e.code==='cancelled'||e.code==='write-failed'",texts[app],app)
        self.assertIn("e?.name==='AbortError'||e.code==='write-failed'",texts['pdf'])
        self.assertIn('if(c.preferShareSave&&c.share)',texts['documents'])
        self.assertIn('if(c.preferShareSave&&c.share)',texts['spreadsheets'])
        self.assertIn('if(isAppleTouchHost()&&canShare(file))',texts['presentations'])
        self.assertIn('if((local||c.preferShareSave)&&c.share)',texts['txt'])
        self.assertIn('if(isAppleTouchHost()&&canShare(file))',texts['pdf'])
        self.assertFalse((ROOT/'shared').exists())
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
        self.assertRegex(presentation_commands,r"register\('file\.save'.*session\.active&&session\.sourceKind!=='ppt'")
        self.assertRegex(presentation_commands,r"register\('file\.share'.*session\.active&&session\.sourceKind!=='ppt'")
        self.assertIn("canExport=isEnabled('file.save')",presentation_commands)
        self.assertIn('saveBtn.disabled=!canExport',presentation_commands)
        self.assertIn("share.disabled=!isEnabled('file.share')",presentation_commands)
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
        pdf_commands=(ROOT/'apps/pdf/ui/command-controller.js').read_text(encoding='utf-8')
        pdf_bindings=(ROOT/'apps/pdf/ui/command-bindings.js').read_text(encoding='utf-8')
        pdf_registry=(ROOT/'apps/pdf/runtime/commands/command-registry.js').read_text(encoding='utf-8')
        self.assertIn("registry.register('file.save',{isEnabled:()=>!!session.active",pdf_commands)
        self.assertIn("registry.register('file.share',{isEnabled:()=>!!session.active",pdf_commands)
        self.assertIn("saveMenuBtn:'file.save'",pdf_bindings)
        self.assertIn("saveToolbarBtn:'file.save'",pdf_bindings)
        self.assertIn("share.dataset.command='file.share'",pdf_bindings)
        self.assertIn('el.disabled=!s.enabled',pdf_registry)
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
