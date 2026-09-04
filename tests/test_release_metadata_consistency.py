from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.version_data = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        cls.version = cls.version_data["version"]
        cls.release_name = cls.version_data["releaseName"]

    def test_public_release_entry_points_match_version_json(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        release_notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("# InkDOS — Ink Desk Offline Suite", readme)
        self.assertTrue(release_notes.startswith(f"# InkDOS v{self.version}"))
        self.assertIn("<title>InkDOS — Ink Desk Offline Suite</title>", home)
        self.assertIn(f"module-registry.js?v={self.version}", home)
        first_heading = next(line for line in changelog.splitlines() if line.startswith("## "))
        self.assertTrue(first_heading.startswith(f"## {self.version}"), first_heading)

    def test_generated_release_metadata_matches_current_version(self):
        for name, key in (
            ("BUILD_INFO.json", "version"),
            ("SOURCE_MANIFEST.json", "version"),
            ("RELEASE_MANIFEST.json", "version"),
            ("package.json", "version"),
        ):
            data = json.loads((ROOT / name).read_text(encoding="utf-8"))
            self.assertEqual(data[key], self.version, name)
        manifest = json.loads((ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["releaseName"], self.release_name)

    def test_public_product_metadata_uses_current_inkdos_urls(self):
        app = json.loads((ROOT / "app-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(app["name"], "InkDOS")
        self.assertEqual(app["source"], self.version_data["repository"])
        self.assertEqual(app["homepage"], self.version_data["demo"])
        self.assertEqual(app["update"]["repository"], "vfydr2m9wk-ops/InkDOS")

    def test_release_history_is_delegated_to_git(self):
        self.assertFalse((ROOT / "docs" / "releases").exists())
        self.assertNotIn("docs/releases", (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
