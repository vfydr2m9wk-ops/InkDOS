from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0-beta.1"


class V100BetaReleaseTests(unittest.TestCase):
    def test_public_beta_identity_is_consistent(self):
        version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        self.assertEqual(version["version"], VERSION)
        self.assertEqual(version["releaseName"], "1.0 Beta 1")
        self.assertEqual(version["releaseChannel"], "beta")
        self.assertEqual(json.loads((ROOT / "package.json").read_text())["version"], VERSION)
        self.assertEqual(json.loads((ROOT / "app-manifest.json").read_text())["version"], VERSION)
        self.assertEqual(json.loads((ROOT / "RELEASE_MANIFEST.json").read_text())["version"], VERSION)

    def test_launcher_generic_open_handoff_is_removed(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        loader = (ROOT / "modules/module-loader.js").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        css = (ROOT / "shared/hub.css").read_text(encoding="utf-8")
        visual = (ROOT / "shared/ui/visual-foundation-v0203.css").read_text(encoding="utf-8")
        for marker in ("Open a supported file", "openAnyDocument", "openAnyInput", "openAnyStatus", "open-any-panel", "shared/hub-open.js"):
            self.assertNotIn(marker, home)
        self.assertFalse((ROOT / "shared/hub-open.js").exists())
        self.assertNotIn("openAnyInput", loader)
        self.assertNotIn("./shared/hub-open.js", worker)
        self.assertNotIn(".open-any-", css)
        self.assertNotIn(".open-any-", visual)

    def test_workspace_open_flows_remain_available(self):
        expected = {
            "documents": "fileInput",
            "spreadsheets": "openBtn",
            "presentations": "openSmall",
            "pdf": "openBtn",
            "txt": "openBtn",
            "epub": "openBtn",
        }
        for module, marker in expected.items():
            html = (ROOT / "apps" / module / "index.html").read_text(encoding="utf-8")
            self.assertIn(marker, html, module)

    def test_release_history_keeps_020_train_as_history(self):
        index = (ROOT / "docs/releases/README.md").read_text(encoding="utf-8")
        self.assertIn(f"[v{VERSION}](RELEASE_NOTES_{VERSION}.md)", index)
        self.assertIn("0.20 development train", index)
        self.assertIn("RELEASE_NOTES_0.20.3.1.md", index)

    def test_internal_sequence_and_public_version_are_separate(self):
        state = json.loads((ROOT / "DEVELOPMENT_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["appliedSequence"], 49)
        self.assertEqual(state["currentPackage"], VERSION)
        # targetRelease is retained as the updater's historical train guard; it is not the public semantic version.
        self.assertEqual(state["targetRelease"], "0.20.x")

    def test_release_integrity_metadata_is_current(self):
        version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        release = version["version"]
        release_date = version["date"]
        manifest = json.loads((ROOT / "app-manifest.json").read_text(encoding="utf-8"))
        sbom = json.loads((ROOT / "SBOM.spdx.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["release"]["version"], release)
        self.assertEqual(manifest["release"]["date"], release_date)
        self.assertNotIn("nextPatch", manifest["update"])
        self.assertNotIn("universalOpenCopy", manifest["homeRefinement"])
        self.assertNotIn("moduleCardsBeforeUniversalOpen", manifest["homeRefinement"])
        self.assertEqual(sbom["name"], f"InkDesk-v{release}")
        self.assertTrue(sbom["documentNamespace"].endswith(f"/tag/v{release}"))
        inkdesk = next(package for package in sbom["packages"] if package["name"] == "InkDesk")
        self.assertEqual(inkdesk["versionInfo"], release)

    def test_release_builder_excludes_generated_browser_results(self):
        import importlib.util

        path = ROOT / "scripts" / "build_release.py"
        spec = importlib.util.spec_from_file_location("inkdesk_build_release", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertTrue(module.is_excluded(Path("tests/browser/results/example.json")))
        self.assertFalse(module.is_excluded(Path("tests/browser/revalidate_v0201_consistency.py")))


if __name__ == "__main__":
    unittest.main()
