from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class VisualFoundationTests(unittest.TestCase):
    def test_foundation_assets_exist(self):
        for relative in (
            'shared/ui/visual-foundation.css',
            'docs/VISUAL_FOUNDATION.md',
            'docs/ICON_SYSTEM.md',
            'assets/icons/icon-catalog.json',
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_bootstrap_loads_foundation_after_workspace_layout(self):
        script = (ROOT / 'shared/office-shell.js').read_text(encoding='utf-8')
        layout = script.index("addStylesheet('workspace-layout.css')")
        foundation = script.index("addStylesheet('visual-foundation.css')")
        self.assertLess(layout, foundation)

    def test_native_apple_like_font_stack_and_rounded_tokens(self):
        tokens = (ROOT / 'shared/ui/design-tokens.css').read_text(encoding='utf-8')
        for marker in (
            '-apple-system',
            'BlinkMacSystemFont',
            'SF Pro Text',
            'Segoe UI Variable Text',
            '--inkdesk-control-height: 36px',
            '--inkdesk-touch-target: 44px',
            '--inkdesk-radius-large: 22px',
        ):
            self.assertIn(marker, tokens)

    def test_tactile_states_and_three_dimensional_panels(self):
        css = (ROOT / 'shared/ui/visual-foundation.css').read_text(encoding='utf-8')
        for marker in (
            'translateY(var(--inkdesk-press-offset)) scale(.975)',
            'button[aria-pressed="true"]',
            'button[aria-selected="true"]',
            'min-height: 50px !important',
            'min-width: 210px !important',
            '.sidebar::after',
            '.slide-list::after',
            '.inspector::before',
            'var(--inkdesk-shadow-panel)',
        ):
            self.assertIn(marker, css)

    def test_icon_inventory_and_dimensions(self):
        names = ('office', 'documents', 'spreadsheets', 'presentations', 'pdf', 'epub', 'txt')
        for name in names:
            svg = ROOT / 'assets' / 'icons' / f'{name}.svg'
            png = ROOT / 'assets' / 'icons' / f'{name}.png'
            self.assertTrue(svg.is_file(), svg)
            self.assertTrue(png.is_file(), png)
            self.assertIn('viewBox="0 0 512 512"', svg.read_text(encoding='utf-8'))
            with Image.open(png) as image:
                self.assertEqual(image.size, (512, 512))
                self.assertEqual(image.mode, 'RGBA')
                self.assertFalse(set(image.info) - {'dpi', 'transparency', 'srgb', 'gamma'})
        self.assertTrue((ROOT / 'assets/icons/office.ico').is_file())

    def test_icon_catalog_marks_future_modules_as_planned(self):
        catalog = json.loads((ROOT / 'assets/icons/icon-catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(catalog['version'], '0.19.4.11')
        self.assertEqual(catalog['icons']['epub']['status'], 'planned')
        self.assertEqual(catalog['icons']['txt']['status'], 'planned')
        self.assertEqual(catalog['icons']['inkdesk']['symbol'], 'quill-and-inkwell')

    def test_launcher_uses_real_module_icon_files(self):
        loader = (ROOT / 'modules/module-loader.js').read_text(encoding='utf-8')
        self.assertIn("iconWrap.className='app-icon has-image'", loader)
        self.assertIn("iconImage.src='./'+module.icon", loader)
        hub = (ROOT / 'shared/hub.css').read_text(encoding='utf-8')
        self.assertIn('../assets/icons/office.svg', hub)
        self.assertIn('../assets/icons/documents.svg', hub)
        self.assertIn('../assets/icons/pdf.svg', hub)

    def test_manifest_and_service_worker_expose_foundation(self):
        manifest = json.loads((ROOT / 'app-manifest.json').read_text(encoding='utf-8'))
        foundation = manifest['uiSystem']['visualFoundation']
        self.assertEqual(foundation['version'], '0.19.4.11')
        self.assertTrue(foundation['raisedRetractablePanels'])
        self.assertEqual(manifest['iconSystem']['version'], '0.19.4.11')
        self.assertIn('epub', manifest['iconSystem']['plannedModuleIcons'])

        worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        for asset in (
            './shared/ui/visual-foundation.css',
            './assets/icons/office.svg',
            './assets/icons/epub.png',
            './assets/icons/txt.png',
            './assets/icons/icon-catalog.json',
        ):
            self.assertIn(repr(asset), worker)
        self.assertRegex(
            worker,
            r"const CACHE_NAME=['\"]inkdesk-shell-v[^'\"]+['\"];",
        )

    def test_module_loader_javascript_syntax(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node.js is unavailable')
        for relative in ('shared/office-shell.js', 'modules/module-loader.js'):
            result = subprocess.run(
                [node, '--check', str(ROOT / relative)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_script_is_registered(self):
        package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
        self.assertEqual(
            package['scripts']['test:visual-foundation'],
            'python3 -m unittest tests.test_visual_foundation',
        )


if __name__ == '__main__':
    unittest.main()
