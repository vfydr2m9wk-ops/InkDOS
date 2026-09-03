from __future__ import annotations

import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))["version"]
        cls.release_name = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))["releaseName"]

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

    def test_release_name_and_historical_note_are_synchronized(self):
        release_notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        historical = ROOT / "docs" / "releases" / f"RELEASE_NOTES_{self.version}.md"
        self.assertTrue(historical.is_file())
        historical_text = historical.read_text(encoding="utf-8")
        self.assertIn(self.release_name, release_notes.splitlines()[0])
        self.assertIn(self.release_name, historical_text.splitlines()[0])

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

    def test_public_product_metadata_uses_inkdos(self):
        for name, key in (("BUILD_INFO.json", "product"), ("SOURCE_MANIFEST.json", "product"), ("RELEASE_MANIFEST.json", "project")):
            self.assertEqual(json.loads((ROOT / name).read_text(encoding="utf-8"))[key], "InkDOS")
        self.assertEqual(json.loads((ROOT / "app-manifest.json").read_text(encoding="utf-8"))["update"]["assetPattern"], "InkDOS_v*.zip")

    def test_release_history_index_starts_with_current_release(self):
        text = (ROOT / "docs" / "releases" / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"^- \[v([^\]]+)\]", text, flags=re.MULTILINE)
        self.assertTrue(links)
        self.assertEqual(links[0], self.version)


if __name__ == "__main__":
    unittest.main()
