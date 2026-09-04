from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
UPDATER = ROOT / "scripts" / "apply_update_package.py"


def load_updater():
    spec = importlib.util.spec_from_file_location("inkdos_updater", UPDATER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class UpdatePackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="inkdos-update-test-")
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "VERSION.json").write_text(json.dumps({"version": "1.0.0-test-base"}))
        (self.repo / "DEVELOPMENT_STATE.json").write_text(json.dumps({
            "schemaVersion": 1,
            "targetRelease": "0.20.x",
            "baseVersion": "0.20.0",
            "appliedSequence": 7,
            "currentPackage": "1.0.0-test-base",
            "status": "complete",
            "history": [{"sequence": n} for n in range(1, 8)],
        }))
        (self.repo / "scripts").mkdir()
        shutil.copy2(UPDATER, self.repo / "scripts" / "apply_update_package.py")
        self.updater = load_updater()

    def tearDown(self):
        self.tmp.cleanup()

    def package(self, manifest: dict, files: dict[str, str], deletions: list[str] | None = None) -> Path:
        package = self.root / "update.zip"
        manifest = json.loads(json.dumps(manifest))
        contract = manifest.setdefault("files", {})
        updater_text = UPDATER.read_text(encoding="utf-8")
        files = {"scripts/apply_update_package.py": updater_text, **files}
        for rel, content in files.items():
            contract[rel] = {"sha256": hashlib.sha256(content.encode()).hexdigest()}
        if deletions:
            manifest["deletions"] = {rel: {} for rel in deletions}
        with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("patch-manifest.json", json.dumps(manifest))
            for rel, content in files.items():
                archive.writestr("files/" + rel, content)
            if deletions:
                archive.writestr("DELETE.txt", "\n".join(deletions) + "\n")
        return package

    def manifest(self) -> dict:
        return {
            "schemaVersion": 2,
            "product": "InkDOS",
            "packageLabel": "1.0.0-test-next",
            "sequence": 8,
            "requires": {"previousSequence": 7, "appVersions": ["1.0.0-test-base"]},
            "description": "test",
            "validationProfile": "none",
        }

    def test_schema1_state_is_compacted_after_successful_update(self):
        (self.repo / "old.txt").write_text("old")
        package = self.package(self.manifest(), {"new.txt": "new"}, ["old.txt"])
        plan = self.updater.apply_package(package, self.repo)
        self.assertEqual(plan["status"], "applied")
        self.assertFalse((self.repo / "old.txt").exists())
        self.assertEqual((self.repo / "new.txt").read_text(), "new")
        state = json.loads((self.repo / "DEVELOPMENT_STATE.json").read_text())
        self.assertEqual(state, {
            "schemaVersion": 2,
            "appliedSequence": 8,
            "currentPackage": "1.0.0-test-next",
            "status": "complete",
        })
        self.assertNotIn("history", state)
        self.assertNotIn("targetRelease", state)
        self.assertNotIn("baseVersion", state)

    def test_candidate_operations_merge_replace_move_and_delete(self):
        (self.repo / "styles").mkdir()
        (self.repo / "styles" / "a.css").write_text(".Ink" + "Desk-a{color:red}\n")
        (self.repo / "styles" / "b.css").write_text(".ink" + "desk-b{color:blue}\n")
        (self.repo / "old-name.py").write_text("VALUE='Ink" + "Desk'\n")
        (self.repo / "obsolete.md").write_text("delete me")
        manifest = self.manifest()
        manifest["operations"] = {
            "fileMerges": [{
                "target": "styles/current.css",
                "sources": ["styles/a.css", "styles/b.css"],
                "deleteSources": True,
            }],
            "treeReplacements": [
                {"old": "Ink" + "Desk", "new": "InkDOS", "minMatches": 1},
                {"old": "ink" + "desk", "new": "inkdos", "minMatches": 1},
            ],
            "moves": {"old-name.py": "current-name.py"},
        }
        package = self.package(manifest, {"marker.txt": "ok"}, ["obsolete.md"])
        self.updater.apply_package(package, self.repo)
        self.assertFalse((self.repo / "styles" / "a.css").exists())
        self.assertFalse((self.repo / "styles" / "b.css").exists())
        css = (self.repo / "styles" / "current.css").read_text()
        self.assertIn("InkDOS-a", css)
        self.assertIn("inkdos-b", css)
        self.assertFalse((self.repo / "old-name.py").exists())
        self.assertEqual((self.repo / "current-name.py").read_text(), "VALUE='InkDOS'\n")
        self.assertFalse((self.repo / "obsolete.md").exists())

    def test_dry_run_validates_without_touching_repository(self):
        package = self.package(self.manifest(), {"new.txt": "new"})
        plan = self.updater.apply_package(package, self.repo, dry_run=True)
        self.assertEqual(plan["status"], "validated")
        self.assertFalse((self.repo / "new.txt").exists())
        state = json.loads((self.repo / "DEVELOPMENT_STATE.json").read_text())
        self.assertEqual(state["appliedSequence"], 7)

    def test_wrong_sequence_is_rejected(self):
        manifest = self.manifest()
        manifest["sequence"] = 9
        package = self.package(manifest, {"new.txt": "new"})
        with self.assertRaises(self.updater.UpdateError):
            self.updater.apply_package(package, self.repo, validation_override="none")

    def test_tree_replacement_base_mismatch_is_transactional(self):
        (self.repo / "sample.txt").write_text("unchanged")
        manifest = self.manifest()
        manifest["operations"] = {
            "treeReplacements": [{"old": "missing-token", "new": "x", "minMatches": 1}]
        }
        package = self.package(manifest, {"marker.txt": "new"})
        with self.assertRaises(self.updater.UpdateError):
            self.updater.apply_package(package, self.repo, validation_override="none")
        self.assertEqual((self.repo / "sample.txt").read_text(), "unchanged")
        self.assertFalse((self.repo / "marker.txt").exists())

    def test_workflow_paths_are_permanently_protected(self):
        with self.assertRaises(self.updater.UpdateError):
            self.updater.safe_relative_path(".github/workflows/unsafe.yml")
        manifest = self.manifest()
        manifest["operations"] = {"moves": {"old.txt": ".github/workflows/new.yml"}}
        (self.repo / "old.txt").write_text("x")
        package = self.package(manifest, {"marker.txt": "new"})
        with self.assertRaises(self.updater.UpdateError):
            self.updater.apply_package(package, self.repo, validation_override="none")

    def test_unsafe_zip_paths_are_rejected(self):
        package = self.root / "unsafe.zip"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr("../escape.txt", "bad")
        with self.assertRaises(self.updater.UpdateError):
            self.updater.extract_package(package, self.root / "out")


if __name__ == "__main__":
    unittest.main()
