#!/usr/bin/env python3
"""Regenerate CHECKSUMS.sha256 for the distributable source tree."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "CHECKSUMS.sha256"
EXCLUDED_PARTS = {".git", ".mobile-import", "__pycache__", "_site", "test-results"}
EXCLUDED_NAMES = {"CHECKSUMS.sha256", "DEVELOPMENT_STATE.json", ".DS_Store", "Thumbs.db"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}


def included_files() -> list[Path]:
    paths: list[Path] = []
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
        paths.append(path)
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def main() -> None:
    lines = [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in included_files()]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} entries to {MANIFEST.name}.")


if __name__ == "__main__":
    main()
