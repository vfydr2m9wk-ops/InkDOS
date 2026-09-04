from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.0.0-beta.4'


class CurrentReleaseTests(unittest.TestCase):
    def test_public_version_is_consistent(self):
        version = json.loads((ROOT / 'VERSION.json').read_text())
        package = json.loads((ROOT / 'package.json').read_text())
        manifest = json.loads((ROOT / 'app-manifest.json').read_text())
        release = json.loads((ROOT / 'RELEASE_MANIFEST.json').read_text())
        self.assertEqual(version['version'], VERSION)
        self.assertEqual(package['version'], VERSION)
        self.assertEqual(manifest['version'], VERSION)
        self.assertEqual(release['version'], VERSION)

    def test_six_modules_are_enabled(self):
        registry = (ROOT / 'modules/module-registry.js').read_text()
        ids = re.findall(r'"id":\s*"([^"]+)"', registry)
        for expected in ('documents', 'spreadsheets', 'presentations', 'pdf', 'txt', 'epub'):
            self.assertIn(expected, ids)

    def test_service_worker_matches_current_baseline(self):
        worker = (ROOT / 'service-worker.js').read_text()
        self.assertIn("const CACHE_NAME='inkdos-shell-v1.0.0-beta.4-ui61';", worker)
        for current in ("visual.css", "content.css", "workspace.css", "polish.css"):
            self.assertIn(repr("./shared/ui/" + current), worker)
        for retired in (
            'visual-foundation-' + 'v0203.css', 'content-workspaces-' + 'v02031.css',
            'workspace-unification-' + 'v02031.css', 'spreadsheets-' + 'beta1-polish.css',
            'light-' + 'only.css',
        ):
            self.assertNotIn(retired, worker)

    def test_development_state_is_compact_current_state(self):
        state = json.loads((ROOT / 'DEVELOPMENT_STATE.json').read_text())
        self.assertEqual(state, {
            'schemaVersion': 2,
            'appliedSequence': 61,
            'currentPackage': VERSION,
            'status': 'complete',
        })

    def test_complete_release_does_not_require_old_packages(self):
        build = json.loads((ROOT / 'BUILD_INFO.json').read_text())
        self.assertFalse(build['requiresPreviousPackages'])
        self.assertEqual(len(build['modules']), 6)


if __name__ == '__main__':
    unittest.main()
