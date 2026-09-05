from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0-beta.8"


class V100BetaReleaseTests(unittest.TestCase):
    def test_public_beta_identity_is_consistent(self):
        version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        self.assertEqual(version["version"], VERSION)
        self.assertEqual(version["releaseName"], "1.0 Beta 8")
        self.assertEqual(version["releaseChannel"], "beta")
        self.assertEqual(version["repository"], "https://github.com/vfydr2m9wk-ops/InkDOS")
        self.assertEqual(version["demo"], "https://vfydr2m9wk-ops.github.io/InkDOS/")

    def test_workspace_open_flows_remain_available(self):
        expected = {"documents": "fileInput", "spreadsheets": "openBtn", "presentations": "openSmall", "pdf": "openBtn", "txt": "openBtn", "epub": "openBtn"}
        for module, marker in expected.items():
            html = (ROOT / "apps" / module / "index.html").read_text(encoding="utf-8")
            self.assertIn(marker, html, module)

    def test_main_tree_does_not_store_release_history(self):
        self.assertFalse((ROOT / "docs" / "releases").exists())
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        headings = [line for line in changelog.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, ["## 1.0.0-beta.8 — 1.0 Beta 8 (2026-09-04)"])

    def test_internal_sequence_is_compact(self):
        state = json.loads((ROOT / "DEVELOPMENT_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["appliedSequence"], 65)
        self.assertEqual(state["currentPackage"], VERSION)
        self.assertNotIn("history", state)
        self.assertNotIn("targetRelease", state)
        self.assertNotIn("baseVersion", state)

    def test_release_integrity_metadata_is_current(self):
        version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "app-manifest.json").read_text(encoding="utf-8"))
        sbom = json.loads((ROOT / "SBOM.spdx.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["release"]["version"], VERSION)
        self.assertEqual(manifest["release"]["date"], version["date"])
        self.assertEqual(manifest["source"], version["repository"])
        self.assertEqual(manifest["homepage"], version["demo"])
        self.assertEqual(sbom["name"], f"InkDOS-v{VERSION}")
        self.assertTrue(sbom["documentNamespace"].endswith(f"/tag/v{VERSION}"))
        inkdos = next(package for package in sbom["packages"] if package["name"] == "InkDOS")
        self.assertEqual(inkdos["versionInfo"], VERSION)

    def test_github_project_metadata_uses_current_identity(self):
        bug = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(encoding="utf-8")
        config = (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
        self.assertIn("InkDOS defect", bug)
        self.assertIn("InkDOS version", bug)
        self.assertIn("vfydr2m9wk-ops/InkDOS/security", config)
        self.assertNotIn("Ink" + "Desk", bug + config)

    def test_current_visual_layers_are_bounded_and_semantic(self):
        shell = (ROOT / "shared" / "office-shell.js").read_text(encoding="utf-8")
        for name in ("visual.css", "content.css", "workspace.css", "polish.css"):
            self.assertIn(repr(name), shell)
            path = ROOT / "shared" / "ui" / name
            self.assertTrue(path.is_file(), name)
            self.assertLessEqual(len(path.read_text(encoding="utf-8").splitlines()), 500, name)
        for retired in (
            "visual-foundation-" + "v0203.css", "content-workspaces-" + "v02031.css",
            "workspace-unification-" + "v02031.css", "spreadsheets-" + "beta1-polish.css",
            "light-" + "only.css",
        ):
            self.assertFalse((ROOT / "shared" / "ui" / retired).exists(), retired)


if __name__ == "__main__":
    unittest.main()
