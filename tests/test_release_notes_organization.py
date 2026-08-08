from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / "docs" / "releases"


class ReleaseNotesOrganizationTests(unittest.TestCase):
    def current_version(self) -> str:
        return json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))["version"]

    def test_historical_release_notes_live_under_docs_releases(self):
        self.assertTrue(RELEASES.is_dir())
        notes = sorted(path.name for path in RELEASES.glob("RELEASE_NOTES_*.md"))
        current = f"RELEASE_NOTES_{self.current_version()}.md"
        self.assertIn("RELEASE_NOTES_0.20.1.md", notes)
        self.assertIn("RELEASE_NOTES_0.20.2.md", notes)
        self.assertIn(current, notes)
        self.assertGreaterEqual(len(notes), 28)

    def test_repository_root_keeps_only_current_release_notes_index(self):
        stray = sorted(path.name for path in ROOT.glob("RELEASE_NOTES_*.md"))
        self.assertEqual(stray, [])
        self.assertTrue((ROOT / "RELEASE_NOTES.md").is_file())

    def test_release_notes_index_points_to_organized_history(self):
        current = f"RELEASE_NOTES_{self.current_version()}.md"
        index = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        releases_index = (RELEASES / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/releases/", index)
        self.assertIn(current, index)
        self.assertIn(current, releases_index)
        self.assertIn("RELEASE_NOTES_0.20.1.md", releases_index)


if __name__ == "__main__":
    unittest.main()
