from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "apply_update_package.py"
SPEC = importlib.util.spec_from_file_location("apply_update_package", MODULE_PATH)
assert SPEC and SPEC.loader
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


class UpdatePackageTests(unittest.TestCase):
    def make_repo(self, root: Path, version: str = "0.19.3-beta.7") -> Path:
        repo = root / "repo"
        repo.mkdir()
        (repo / "VERSION.json").write_text(
            json.dumps({"name": "InkDesk", "version": version}) + "\n",
            encoding="utf-8",
        )
        (repo / "keep.txt").write_text("original\n", encoding="utf-8")
        return repo

    def make_package(
        self,
        root: Path,
        *,
        sequence: int = 1,
        previous: int = 0,
        validation: str = "none",
        files: dict[str, bytes | str] | None = None,
        deletes: list[str] | None = None,
        archive_name: str = "update.zip",
    ) -> Path:
        package = root / archive_name
        manifest = {
            "schemaVersion": 1,
            "product": "InkDesk",
            "targetRelease": "0.19.4",
            "packageLabel": f"0.19.4.{sequence}",
            "sequence": sequence,
            "requires": {
                "previousSequence": previous,
                "appVersions": ["0.19.3-beta.7"],
            },
            "description": "Synthetic updater test",
            "validationProfile": validation,
        }
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("patch-manifest.json", json.dumps(manifest))
            for name, value in (files or {"example.txt": "updated\n"}).items():
                archive.writestr(f"files/{name}", value)
            if deletes:
                archive.writestr("DELETE.txt", "\n".join(deletes) + "\n")
        return package

    def test_applies_files_and_writes_sequence_state(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            package = self.make_package(
                root,
                files={"keep.txt": "replaced\n", "new/feature.txt": "new\n"},
            )
            report = updater.apply_package(package, repo)
            self.assertEqual((repo / "keep.txt").read_text(), "replaced\n")
            self.assertEqual((repo / "new/feature.txt").read_text(), "new\n")
            state = json.loads((repo / "DEVELOPMENT_STATE.json").read_text())
            self.assertEqual(state["appliedSequence"], 1)
            self.assertEqual(state["currentPackage"], "0.19.4.1")
            self.assertEqual(report["sequence"], 1)

    def test_requires_strict_sequence_order(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            package = self.make_package(root, sequence=2, previous=1)
            with self.assertRaises(updater.UpdateError):
                updater.apply_package(package, repo)

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            package = root / "unsafe.zip"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("patch-manifest.json", "{}")
                archive.writestr("files/../../escaped.txt", "bad")
            with self.assertRaises(updater.UpdateError):
                updater.apply_package(package, repo)
            self.assertFalse((root / "escaped.txt").exists())

    def test_workflow_file_changes_are_always_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            package = self.make_package(
                root,
                files={".github/workflows/new.yml": "name: test\n"},
            )
            with self.assertRaisesRegex(
                updater.UpdateError,
                "cannot create, modify, or delete GitHub workflow files",
            ):
                updater.apply_package(package, repo)
            self.assertFalse((repo / ".github/workflows/new.yml").exists())

    def test_workflow_file_deletions_are_always_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            package = self.make_package(
                root,
                files={"regular.txt": "ok\n"},
                deletes=[".github/workflows/existing.yml"],
            )
            with self.assertRaisesRegex(
                updater.UpdateError,
                "cannot create, modify, or delete GitHub workflow files",
            ):
                updater.apply_package(package, repo)

    def test_validation_failure_restores_original_files(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            package = self.make_package(
                root,
                validation="standard",
                files={"keep.txt": "must be rolled back\n", "new.txt": "temporary\n"},
            )
            captured = io.StringIO()
            with mock.patch.object(updater, "run_validation", side_effect=RuntimeError("synthetic validation failure")):
                with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
                    with self.assertRaises(Exception):
                        updater.apply_package(package, repo)
            self.assertEqual((repo / "keep.txt").read_text(), "original\n")
            self.assertFalse((repo / "new.txt").exists())
            self.assertFalse((repo / "DEVELOPMENT_STATE.json").exists())

    def test_dry_run_validates_disposable_candidate_without_changing_repository(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            package = self.make_package(
                root,
                validation="standard",
                files={"keep.txt": "changed\n", "new.txt": "candidate only\n"},
            )
            observed = {}

            def inspect_candidate(candidate, profile):
                observed["candidate"] = candidate
                observed["profile"] = profile
                observed["keep"] = (candidate / "keep.txt").read_text()
                observed["new"] = (candidate / "new.txt").read_text()
                observed["state"] = json.loads(
                    (candidate / "DEVELOPMENT_STATE.json").read_text()
                )
                self.assertNotEqual(candidate.resolve(), repo.resolve())
                self.assertEqual((repo / "keep.txt").read_text(), "original\n")
                self.assertFalse((repo / "new.txt").exists())

            captured = io.StringIO()
            with mock.patch.object(updater, "run_validation", side_effect=inspect_candidate):
                with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
                    report = updater.apply_package(package, repo, dry_run=True)

            self.assertEqual(observed["profile"], "standard")
            self.assertEqual(observed["keep"], "changed\n")
            self.assertEqual(observed["new"], "candidate only\n")
            self.assertEqual(observed["state"]["appliedSequence"], 1)
            self.assertFalse(observed["candidate"].exists())
            self.assertEqual((repo / "keep.txt").read_text(), "original\n")
            self.assertFalse((repo / "new.txt").exists())
            self.assertFalse((repo / "DEVELOPMENT_STATE.json").exists())
            self.assertTrue(report["dryRun"])
            self.assertTrue(report["validatedCandidate"])
            self.assertEqual(report["status"], "validated")
            self.assertEqual(report["packageSha256"], updater.sha256_file(package))

    def test_dry_run_validation_failure_leaves_source_repository_untouched(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            package = self.make_package(
                root,
                validation="standard",
                files={"keep.txt": "candidate failure\n", "new.txt": "temporary\n"},
            )
            with mock.patch.object(
                updater,
                "run_validation",
                side_effect=RuntimeError("synthetic dry-run validation failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "synthetic dry-run"):
                    updater.apply_package(package, repo, dry_run=True)
            self.assertEqual((repo / "keep.txt").read_text(), "original\n")
            self.assertFalse((repo / "new.txt").exists())
            self.assertFalse((repo / "DEVELOPMENT_STATE.json").exists())

    def test_delete_list_removes_only_declared_path(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repo = self.make_repo(root)
            (repo / "remove.txt").write_text("remove\n")
            package = self.make_package(
                root,
                files={"new.txt": "new\n"},
                deletes=["remove.txt"],
            )
            updater.apply_package(package, repo)
            self.assertFalse((repo / "remove.txt").exists())
            self.assertTrue((repo / "keep.txt").exists())

    def test_full_validation_profile_is_single_pass(self):
        commands = [" ".join(command) for command in updater.VALIDATION_PROFILES["full"]]
        self.assertEqual(sum("scripts/run_release_validation.py" in command for command in commands), 1)
        self.assertFalse(any("unittest" in command for command in commands))
        self.assertFalse(any("scripts/validate_repository.py" in command for command in commands))
        self.assertFalse(any("scripts/audit_source.py" in command for command in commands))

    def test_workflow_avoids_privacy_audit_local_paths(self):
        workflow_path = ROOT / ".github/workflows/apply-inkdesk-update.yml"
        text = workflow_path.read_text(encoding="utf-8").lower()
        forbidden_terms = (
            "/mnt/" + "data",
            "/tmp/" + "inkdesk",
            "/home/" + "oai",
            "file:///" + "users/",
            "local office " + "suite",
            "external display " + "browser",
        )
        for forbidden in forbidden_terms:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
