from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReleasePackagingTests(unittest.TestCase):
    def build(self, output: Path) -> Path:
        subprocess.run(
            [sys.executable, "scripts/build_release.py", "--output-dir", str(output), "--commit", "0123456789abcdef", "--tag", "v-test"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))["version"]
        return output / f"InkDesk_v{version}.zip"

    def test_runtime_archive_is_reproducible_and_scoped(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            archive_a = self.build(Path(first))
            archive_b = self.build(Path(second))
            self.assertEqual(archive_a.read_bytes(), archive_b.read_bytes())
            with zipfile.ZipFile(archive_a) as package:
                names = package.namelist()
                self.assertEqual(names, sorted(names))
                for required in (
                    "BUILD_INFO.json",
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
                self.assertEqual(build["commit"], "0123456789abcdef")
                self.assertEqual(build["tag"], "v-test")
                checksums = package.read("RUNTIME_CHECKSUMS.sha256").decode().splitlines()
                expected = {}
                for line in checksums:
                    checksum, name = line.split("  ", 1)
                    expected[name] = checksum
                for name, checksum in expected.items():
                    self.assertEqual(hashlib.sha256(package.read(name)).hexdigest(), checksum)


if __name__ == "__main__":
    unittest.main()
