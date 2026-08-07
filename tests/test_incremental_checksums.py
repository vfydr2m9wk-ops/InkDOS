from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "update_checksums_incrementally.py"
SPEC = importlib.util.spec_from_file_location("update_checksums_incrementally", MODULE_PATH)
assert SPEC and SPEC.loader
checksums = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checksums)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class IncrementalChecksumTests(unittest.TestCase):
    def make_tree(self, root: Path) -> tuple[Path, Path]:
        repo = root / "repo"
        repo.mkdir()
        (repo / "a.txt").write_text("a-old\n", encoding="utf-8")
        (repo / "b.txt").write_text("b-stable\n", encoding="utf-8")
        (repo / "c.txt").write_text("c-delete\n", encoding="utf-8")
        manifest = repo / "CHECKSUMS.sha256"
        manifest.write_text(
            "".join(
                [
                    f"{checksums.digest(repo / 'a.txt')}  a.txt\n",
                    f"{checksums.digest(repo / 'b.txt')}  b.txt\n",
                    f"{checksums.digest(repo / 'c.txt')}  c.txt\n",
                    # This deliberately represents a hosted-only file that is
                    # absent from the local tree. Incremental updates must keep it.
                    f"{'f' * 64}  hosted-only.bin\n",
                ]
            ),
            encoding="utf-8",
        )
        return repo, manifest

    def test_updates_only_declared_paths_and_preserves_hosted_only_hashes(self):
        with tempfile.TemporaryDirectory() as name:
            repo, manifest = self.make_tree(Path(name))
            (repo / "a.txt").write_text("a-new\n", encoding="utf-8")
            (repo / "new.txt").write_text("new\n", encoding="utf-8")
            (repo / "c.txt").unlink()

            before = checksums.load_manifest(manifest)
            after = checksums.update_manifest(
                repo,
                manifest,
                changed=["a.txt", "new.txt"],
                deleted=["c.txt"],
            )

            self.assertEqual(after["a.txt"], checksums.digest(repo / "a.txt"))
            self.assertEqual(after["new.txt"], checksums.digest(repo / "new.txt"))
            self.assertNotIn("c.txt", after)
            self.assertEqual(after["b.txt"], before["b.txt"])
            self.assertEqual(after["hosted-only.bin"], "f" * 64)

    def test_missing_changed_path_requires_explicit_delete(self):
        with tempfile.TemporaryDirectory() as name:
            repo, manifest = self.make_tree(Path(name))
            (repo / "a.txt").unlink()
            with self.assertRaisesRegex(checksums.ChecksumUpdateError, "use --delete"):
                checksums.update_manifest(repo, manifest, changed=["a.txt"], deleted=[])

    def test_changed_and_deleted_overlap_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            repo, manifest = self.make_tree(Path(name))
            with self.assertRaisesRegex(checksums.ChecksumUpdateError, "both changed and deleted"):
                checksums.update_manifest(repo, manifest, changed=["a.txt"], deleted=["a.txt"])

    def test_excluded_files_cannot_be_added_to_manifest(self):
        with tempfile.TemporaryDirectory() as name:
            repo, manifest = self.make_tree(Path(name))
            (repo / "temporary.zip").write_bytes(b"zip")
            with self.assertRaisesRegex(checksums.ChecksumUpdateError, "excluded"):
                checksums.update_manifest(repo, manifest, changed=["temporary.zip"], deleted=[])


if __name__ == "__main__":
    unittest.main()
