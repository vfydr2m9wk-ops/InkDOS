from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ConsolidatedReleaseTests(unittest.TestCase):
    def test_public_version_is_consistent(self):
        version = json.loads((ROOT / 'VERSION.json').read_text())
        package = json.loads((ROOT / 'package.json').read_text())
        manifest = json.loads((ROOT / 'app-manifest.json').read_text())
        release = json.loads((ROOT / 'RELEASE_MANIFEST.json').read_text())
        self.assertEqual(version['version'], '0.20.2.30')
        self.assertEqual(package['version'], '0.20.2.30')
        self.assertEqual(manifest['version'], '0.20.2.30')
        self.assertEqual(release['version'], '0.20.2.30')

    def test_six_modules_are_enabled(self):
        registry = (ROOT / 'modules/module-registry.js').read_text()
        ids = re.findall(r'"id":\s*"([^"]+)"', registry)
        for expected in (
            'documents', 'spreadsheets', 'presentations',
            'pdf', 'txt', 'epub'
        ):
            self.assertIn(expected, ids)

    def test_home_has_clean_six_workspace_layout(self):
        html = (ROOT / 'index.html').read_text()
        self.assertIn('class="workspace-grid"', html)
        self.assertIn('InkDesk v0.20.2.30', html)
        self.assertIn('The selected file stays on this device.', html)
        self.assertNotIn('Choose a DOCX, XLS, XLSX', html)
        self.assertNotIn('0.19.4.15', html)
        for workspace in (
            'Documents', 'Spreadsheets', 'Presentations',
            'PDF Workspace', 'Plain Text', 'EPUB Reader'
        ):
            self.assertIn(workspace, html)

    def test_service_worker_matches_public_version(self):
        worker = (ROOT / 'service-worker.js').read_text()
        self.assertIn("const CACHE_NAME='inkdesk-shell-v0.20.2.30';", worker)
        for asset in (
            "'./apps/txt/index.html'",
            "'./apps/epub/index.html'",
            "'./PDF.html'",
            "'./TXT.html'",
            "'./EPUB.html'",
        ):
            self.assertIn(asset, worker)

    def test_development_state_is_reset_for_patch_series(self):
        state = json.loads((ROOT / 'DEVELOPMENT_STATE.json').read_text())
        self.assertEqual(state['targetRelease'], '0.20.x')
        self.assertEqual(state['appliedSequence'], 32)
        self.assertEqual(state['currentPackage'], '0.20.2.30')

    def test_complete_release_does_not_require_old_packages(self):
        build = json.loads((ROOT / 'BUILD_INFO.json').read_text())
        self.assertFalse(build['requiresPreviousPackages'])
        self.assertEqual(len(build['modules']), 6)


if __name__ == '__main__':
    unittest.main()
