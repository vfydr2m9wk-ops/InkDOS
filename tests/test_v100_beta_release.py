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
        self.assertEqual(state["appliedSequence"], 47)
        self.assertEqual(state["currentPackage"], VERSION)
        # targetRelease is retained as the updater's historical train guard; it is not the public semantic version.
        self.assertEqual(state["targetRelease"], "0.20.x")


if __name__ == "__main__":
    unittest.main()
