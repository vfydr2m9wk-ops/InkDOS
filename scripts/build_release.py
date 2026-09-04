#!/usr/bin/env python3
"""Build a deterministic complete InkDOS source archive."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", "__pycache__", "test-results", "dist"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
EXCLUDED_PATH_PREFIXES = {("tests", "browser", "results")}


def is_excluded(relative: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return True
    if any(relative.parts[: len(prefix)] == prefix for prefix in EXCLUDED_PATH_PREFIXES):
        return True
    return relative.suffix.lower() in EXCLUDED_SUFFIXES


def included_files() -> list[Path]:
    result = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if is_excluded(relative):
            continue
        result.append(path)
    return sorted(result, key=lambda p: p.relative_to(ROOT).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="dist")
    args = parser.parse_args()

    required_vendor = [
        ROOT / "shared/vendor/pdfjs/pdf.min.js",
        ROOT / "shared/vendor/pdfjs/pdf.worker.min.js",
        ROOT / "shared/vendor/pdfjs/LICENSE-PDFJS.txt",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required_vendor if not path.is_file()]
    if missing:
        print(
            "Release build requires the publication-vendored PDF.js files: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        return 2

    commands = [
        [sys.executable, "scripts/generate_release_metadata.py"],
        [sys.executable, "scripts/generate_module_registry.py", "--check"],
        [sys.executable, "scripts/check_no_legacy_runtime.py"],
        [sys.executable, "scripts/validate_repository.py"],
        [sys.executable, "scripts/audit_source.py"],
        [sys.executable, "scripts/generate_checksums.py"],
        [sys.executable, "scripts/verify_checksums.py"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode

    version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))["version"]
    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"InkDOS_v{version}.zip"

    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in included_files():
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 8, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (archive_path.with_suffix(archive_path.suffix + ".sha256")).write_text(
        f"{digest}  {archive_path.name}\n",
        encoding="utf-8",
    )
    print(archive_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
