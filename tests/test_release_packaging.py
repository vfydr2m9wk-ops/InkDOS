from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleasePackagingTests(unittest.TestCase):
    def make_tagged_checkout(self, directory: Path) -> Path:
        checkout = directory / "checkout"
        shutil.copytree(
            ROOT,
            checkout,
            ignore=shutil.ignore_patterns(".git", "dist", "__pycache__", "*.pyc", "test-results"),
        )
        subprocess.run(["git", "init"], cwd=checkout, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "inkdesk-tests@example.invalid"], cwd=checkout, check=True)
        subprocess.run(["git", "config", "user.name", "InkDesk Tests"], cwd=checkout, check=True)
        subprocess.run(["git", "add", "."], cwd=checkout, check=True)
        subprocess.run(["git", "commit", "-m", "test checkout"], cwd=checkout, check=True, capture_output=True, text=True)
        version = json.loads((checkout / "VERSION.json").read_text(encoding="utf-8"))["version"]
        subprocess.run(["git", "tag", f"v{version}"], cwd=checkout, check=True)
        return checkout

    def build(self, checkout: Path, output: Path) -> Path:
        subprocess.run(
            [sys.executable, "scripts/build_release.py", "--output-dir", str(output)],
            cwd=checkout,
            check=True,
            capture_output=True,
            text=True,
        )
        version = json.loads((checkout / "VERSION.json").read_text(encoding="utf-8"))["version"]
        return output / f"InkDesk_v{version}.zip"

    def test_runtime_archive_is_reproducible_scoped_and_traceable(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            base = Path(temporary)
            checkout = self.make_tagged_checkout(base)
            archive_a = self.build(checkout, base / "first")
            archive_b = self.build(checkout, base / "second")
            self.assertEqual(archive_a.read_bytes(), archive_b.read_bytes())
            with zipfile.ZipFile(archive_a) as package:
                names = package.namelist()
                self.assertEqual(names, sorted(names))
                for required in (
                    "BUILD_INFO.json",
                    "SOURCE_MANIFEST.json",
                    "SBOM.spdx.json",
                    "RUNTIME_CHECKSUMS.sha256",
                    "LICENSE",
                    "docs/THIRD_PARTY_NOTICES.md",
                    "shared/vendor/LICENSE-JSZIP.txt",
                    "shared/vendor/LICENSE-PAKO.txt",
                    "RELEASE_NOTES.md",
                    "RELEASE_TEST_REPORT.md",
                    "UPGRADE_NOTES.md",
                ):
                    self.assertIn(required, names)
                self.assertFalse(any(name.startswith((".git/", ".github/", "tests/", "scripts/")) for name in names))
                self.assertFalse(any(name.endswith(".zip") for name in names))
                build = json.loads(package.read("BUILD_INFO.json"))
                head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
                version = json.loads((checkout / "VERSION.json").read_text(encoding="utf-8"))["version"]
                self.assertEqual(build["commit"], head)
                self.assertEqual(build["tag"], f"v{version}")
                self.assertTrue(build["gitTreeClean"])
                self.assertTrue(build["tagMatchesHead"])
                manifest = json.loads(package.read("SOURCE_MANIFEST.json"))
                self.assertGreater(len(manifest["files"]), 50)
                sbom = json.loads(package.read("SBOM.spdx.json"))
                self.assertEqual(sbom["spdxVersion"], "SPDX-2.3")
                self.assertGreaterEqual(len(sbom["packages"]), 3)
                checksums = package.read("RUNTIME_CHECKSUMS.sha256").decode().splitlines()
                expected = {}
                for line in checksums:
                    checksum, name = line.split("  ", 1)
                    expected[name] = checksum
                for name, checksum in expected.items():
                    self.assertEqual(hashlib.sha256(package.read(name)).hexdigest(), checksum)

    def test_build_refuses_dirty_or_untagged_checkout(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            base = Path(temporary)
            checkout = self.make_tagged_checkout(base)
            (checkout / "README.md").write_text("dirty\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "scripts/build_release.py", "--output-dir", str(base / "dirty-build")],
                cwd=checkout,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("clean working tree", result.stderr)

            subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=checkout, check=True, capture_output=True)
            version = json.loads((checkout / "VERSION.json").read_text(encoding="utf-8"))["version"]
            subprocess.run(["git", "tag", "-d", f"v{version}"], cwd=checkout, check=True, capture_output=True)
            result = subprocess.run(
                [sys.executable, "scripts/build_release.py", "--output-dir", str(base / "untagged-build")],
                cwd=checkout,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Required tag", result.stderr)


if __name__ == "__main__":
    unittest.main()
