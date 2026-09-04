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
        self.assertIn('"registryVersion": "1.0.0-beta.5"',registry)

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

    def test_update_pipeline_contract_remains_intact(self):
        updater=(ROOT/'scripts/apply_update_package.py').read_text(encoding='utf-8')
        for marker in ('class UpdateError', 'def apply_package(', 'def write_failure_report(', 'Stable update packages cannot create, modify, or delete GitHub workflow files.'):
            self.assertIn(marker,updater)
        self.assertTrue((ROOT/'.github/workflows/apply-inkdos-update.yml').is_file())


if __name__=='__main__':unittest.main()
