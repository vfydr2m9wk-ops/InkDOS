from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
APPS=('documents','spreadsheets','presentations','pdf','txt','epub')

class RefinementCheckpointTests(unittest.TestCase):
    def test_registry_has_product_identity_and_actions(self):
        for app_id in APPS:
            data=json.loads((ROOT/'apps'/app_id/'module.json').read_text(encoding='utf-8'))
            for key in ('label','shortLabel','route','extensions','capabilities','createAction','openAction','openLabel'):
                self.assertIn(key,data,app_id)
            self.assertEqual(data['route'],data['entryPoint'])
            self.assertEqual(data['openAction'],'fileInput')
        self.assertIsNone(json.loads((ROOT/'apps/pdf/module.json').read_text())['createAction'])
        self.assertIsNone(json.loads((ROOT/'apps/epub/module.json').read_text())['createAction'])
    def test_generated_registry_contains_shared_identity_and_actions(self):
        registry=(ROOT/'modules/module-registry.js').read_text(encoding='utf-8')
        for marker in ('"label":', '"shortLabel":', '"route":', '"createAction":', '"openAction":', '"openLabel":'):
            self.assertIn(marker,registry)
        self.assertIn('"registryVersion": "1.0.0-beta.10"',registry)

    def test_shared_surfaces_are_present_and_offline(self):
        for path in ('shared/recent-files.js','shared/app-shell.js','shared/app-home.js','shared/ui/app-shell.css','shared/ui/app-home.css','shared/ui/refinement-home.css'):
            self.assertTrue((ROOT/path).is_file(),path)
        worker=(ROOT/'service-worker.js').read_text(encoding='utf-8')
        for path in ('./shared/recent-files.js','./shared/app-shell.js','./shared/app-home.js','./shared/ui/app-shell.css','./shared/ui/app-home.css','./shared/ui/refinement-home.css'):
            self.assertIn(repr(path),worker)
    def test_apps_boot_shared_apphome(self):
        for app_id in APPS:
            html=(ROOT/'apps'/app_id/'index.html').read_text(encoding='utf-8')
            self.assertIn('data-inkdos-app="'+app_id+'"',html)
            self.assertIn('data-app-home',html)
            self.assertIn('../../shared/app-home.js',html)
            self.assertIn('../../shared/app-shell.js',html)
    def test_home_boots_recent_and_global_shell(self):
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('./shared/recent-files.js',html)
        self.assertIn('./shared/app-shell.js',html)
        shell=(ROOT/'shared/suite-shell.js').read_text(encoding='utf-8')
        self.assertIn("doc.querySelector('.hub-intro')?.remove()",shell)
        self.assertIn("runtime.listEnabled().forEach",shell)
        self.assertIn("data-recent-filters",shell)
        self.assertIn('class="suite-action primary recent-open"',shell)
        app_shell=(ROOT/'shared/app-shell.js').read_text(encoding='utf-8')
        app_shell_css=(ROOT/'shared/ui/app-shell.css').read_text(encoding='utf-8')
        self.assertIn("topbar.dataset.inkdosShellRegion='titlebar'",shell)
        self.assertIn("if(oldMenu)oldMenu.remove()",shell)
        self.assertNotIn("oldMenu.dataset.appLauncherTrigger",shell)
        self.assertNotIn("settings.className='suite-menu",shell)
        self.assertIn("button.className='icon-btn inkdos-global-trigger'",app_shell)
        self.assertIn("global.InkDOSAppShell.refreshTriggers",shell)
        self.assertIn('.inkdos-global-trigger{',app_shell_css)
        self.assertIn('transition:transform .09s ease,box-shadow .12s ease!important',app_shell_css)
        self.assertNotIn("function syncHomeControlTheme()",shell)
        self.assertNotIn("new MutationObserver(syncHomeControlTheme)",shell)
    def test_recent_service_is_metadata_only(self):
        text=(ROOT/'shared/recent-files.js').read_text(encoding='utf-8')
        for marker in ('registerOpened','registerCreated','touch','remove','clear','resolveFile'):
            self.assertIn(marker,text)
        self.assertNotIn('arrayBuffer()',text)
        self.assertNotIn('FileReader',text)
    def test_global_actions_use_existing_titlebar_left_region(self):
        shell=(ROOT/'shared/app-shell.js').read_text(encoding='utf-8')
        self.assertIn(".txt-title-actions,.titlebar-left",shell)
        self.assertNotIn(".txt-title-actions')||bar",shell)

    def test_mobile_home_theme_and_gutter_contract(self):
        css=(ROOT/'shared/ui/refinement-home.css').read_text(encoding='utf-8')
        for marker in ('--suite-surface:var(--surface)', '--suite-text:var(--text)', '--surface-soft:#20252d', 'padding-left:max(20px,env(safe-area-inset-left))', 'padding-right:max(20px,env(safe-area-inset-right))'):
            self.assertIn(marker,css)
        self.assertIn('border:1px solid var(--border)',css)
        self.assertIn('background:var(--recent-filter-accent,#757575)',css)
        shell=(ROOT/'shared/suite-shell.js').read_text(encoding='utf-8')
        self.assertIn("recentFilterAccents=Object.freeze({",shell)
        for accent in ('#2e6fed','#2a854c','#cf4723','#e12c1e','#93700e','#8163cb'):
            self.assertIn(accent,shell)
        self.assertIn("button.style.setProperty('--recent-filter-accent'",shell)
        neutral_block=css.split('.recent-filter{',1)[1].split('.recent-filter[aria-pressed=true]',1)[0]
        self.assertNotIn('--recent-filter-accent',neutral_block)
        self.assertIn('html[data-theme="dark"] .recent-filter[aria-pressed=true]',css)
        self.assertIn('.brand-mark{width:48px;height:48px}',css)
        self.assertIn('.brand-copy strong{font-size:20px}',css)
        self.assertIn('font-size:clamp(23px,2.6vw,28px)',css)
        self.assertIn('font-size:24px',css)
        responsive_css=(ROOT/'shared/ui/responsive-workspace.css').read_text(encoding='utf-8')
        responsive_js=(ROOT/'shared/responsive-command-menu.js').read_text(encoding='utf-8')
        self.assertIn('inkdos-command-trigger',responsive_css)
        self.assertIn('@media(orientation:portrait)',responsive_css)
        self.assertIn('grid-template-rows:minmax(0,1fr) 132px!important',responsive_css)
        self.assertIn('padding-left:max(12px,env(safe-area-inset-left))!important',responsive_css)
        self.assertIn('padding-right:max(12px,env(safe-area-inset-right))!important',responsive_css)
        app_home=(ROOT/'shared/app-home.js').read_text(encoding='utf-8')
        self.assertIn("host.classList.remove('start-screen')",app_home)
        for command in ('home','save','new','share','undo','redo'):
            self.assertIn("['"+command+"'",responsive_js)
        for app_id in APPS:
            html=(ROOT/'apps'/app_id/'index.html').read_text(encoding='utf-8')
            self.assertIn('../../shared/ui/responsive-workspace.css',html)
            self.assertIn('../../shared/responsive-command-menu.js',html)

    def test_apphome_is_a_viewport_level_surface(self):
        shell=(ROOT/'shared/app-home.js').read_text(encoding='utf-8')
        css=(ROOT/'shared/ui/app-home.css').read_text(encoding='utf-8')
        self.assertIn("if(host.parentElement!==doc.body)doc.body.appendChild(host)",shell)
        for marker in ('position:fixed!important', 'inset:0!important', 'width:100vw!important', 'height:100dvh!important', 'overflow:auto!important'):
            self.assertIn(marker,css)
        self.assertNotIn('body.inkdos-app-home-active.office-documents .workspace',css)
        self.assertNotIn('grid-template-columns:minmax(0,1fr)!important',css)
        self.assertIn('display:block!important',css)
        self.assertIn("module.createLabel||'Create','inkdos-app-home-action'",shell)
        self.assertIn("module.openLabel||'Open file','inkdos-app-home-action inkdos-app-home-action-primary'",shell)
        self.assertIn('background:#fff!important;color:#1f2937!important',css)
        self.assertIn('.inkdos-app-home-action-primary{border-color:#2f6fed!important;background:#2f6fed!important;color:#fff!important}',css)

    def test_update_pipeline_contract_remains_intact(self):
        updater=(ROOT/'scripts/apply_update_package.py').read_text(encoding='utf-8')
        for marker in ('class UpdateError', 'def apply_package(', 'def write_failure_report(', 'Stable update packages cannot create, modify, or delete GitHub workflow files.'):
            self.assertIn(marker,updater)
        self.assertTrue((ROOT/'.github/workflows/apply-inkdos-update.yml').is_file())


if __name__=='__main__':unittest.main()
