#!/usr/bin/env python3
"""Verify CHECKSUMS.sha256 and its coverage of the distributable tree."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "CHECKSUMS.sha256"
LINE_PATTERN = re.compile(r"^([0-9a-fA-F]{64})  (.+)$")
EXCLUDED_PARTS = {".git", ".mobile-import", "__pycache__", "_site", "test-results"}
EXCLUDED_NAMES = {"CHECKSUMS.sha256", "DEVELOPMENT_STATE.json", "package-lock.json", ".DS_Store", "Thumbs.db"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}


def included_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative.parts[:3] == ("tests", "browser", "results"):
            continue
        if relative.name in EXCLUDED_NAMES or relative.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        files[relative.as_posix()] = path
    return files


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main() -> int:
    errors: list[str] = []
    expected: dict[str, str] = {}

    if not MANIFEST.is_file():
        print("Checksum verification failed: CHECKSUMS.sha256 is missing.")
        return 1

    for number, raw_line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        match = LINE_PATTERN.fullmatch(raw_line)
        if not match:
            errors.append(f"Invalid checksum line {number}: {raw_line}")
            continue
        checksum, relative = match.groups()
        if relative in expected:
            errors.append(f"Duplicate checksum entry: {relative}")
            continue
        expected[relative] = checksum.lower()

    actual = included_files()
    for relative, checksum in expected.items():
        path = actual.get(relative)
        if path is None:
            errors.append(f"Manifest entry is missing from the tree: {relative}")
            continue
        observed = digest(path)
        if observed != checksum:
            errors.append(f"Checksum mismatch: {relative}")

    for relative in sorted(set(actual) - set(expected)):
        errors.append(f"File is not covered by CHECKSUMS.sha256: {relative}")

    if errors:
        print("Checksum verification failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Checksum verification passed ({len(expected)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
