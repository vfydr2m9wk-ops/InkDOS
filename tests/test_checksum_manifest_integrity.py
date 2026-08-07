#!/usr/bin/env python3
"""Fail fast when CHECKSUMS.sha256 diverges from the candidate repository tree."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ChecksumManifestIntegrityTests(unittest.TestCase):
    def test_checksum_manifest_matches_candidate_tree(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/verify_checksums.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        message = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        self.assertEqual(result.returncode, 0, message)


if __name__ == "__main__":
    unittest.main()
