#!/usr/bin/env python3
"""Build a deterministic InkDesk runtime ZIP from the current checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
ROOT_FILES = {
    ".nojekyll",
    "CHANGELOG.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "COMPATIBILITY.md",
    "CONTRIBUTING.md",
    "DEVELOPMENT.md",
    "Documents.html",
    "InkDesk.html",
    "LICENSE",
    "Presentations.html",
    "README.md",
    "RELEASE_MANIFEST.json",
    "RELEASE_NOTES.md",
    "RELEASE_TEST_REPORT.md",
    "SECURITY.md",
    "Spreadsheets.html",
    "SUPPORT.md",
    "TESTING.md",
    "UPGRADE_NOTES.md",
    "VERSION.json",
    "app-manifest.json",
    "index.html",
    "manifest.webmanifest",
    "package.json",
    "service-worker.js",
}
RUNTIME_DIRS = ("apps", "assets", "docs", "shared")
EXCLUDED_PARTS = {"__pycache__", "results", ".git", "node_modules", "dist", "_site"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def included_paths() -> list[Path]:
    paths: list[Path] = []
    for name in sorted(ROOT_FILES):
        path = ROOT / name
        if path.is_file():
            paths.append(path)
    for directory in RUNTIME_DIRS:
        for path in (ROOT / directory).rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            paths.append(path)
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(PurePosixPath(name).as_posix(), FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="dist")
    parser.add_argument("--commit", default=None)
    parser.add_argument("--tag", default=None)
    args = parser.parse_args()

    version_doc = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
    version = str(version_doc["version"])
    commit = args.commit or git_value("rev-parse", "HEAD")
    tag = args.tag or f"v{version}"
    output = (ROOT / args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"InkDesk_v{version}.zip"

    members: dict[str, bytes] = {}
    for path in included_paths():
        members[path.relative_to(ROOT).as_posix()] = path.read_bytes()

    build_info = {
        "project": "InkDesk",
        "version": version,
        "releaseChannel": version_doc.get("releaseChannel", "beta"),
        "tag": tag,
        "commit": commit,
        "sourceRepository": version_doc.get("repository"),
        "reproducibleArchive": True,
        "archiveTimestamp": "1980-01-01T00:00:00Z",
    }
    members["BUILD_INFO.json"] = (json.dumps(build_info, indent=2, sort_keys=True) + "\n").encode()
    runtime_checksums = "".join(f"{digest(data)}  {name}\n" for name, data in sorted(members.items()))
    members["RUNTIME_CHECKSUMS.sha256"] = runtime_checksums.encode()

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as package:
        for name, data in sorted(members.items()):
            package.writestr(zip_info(name), data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    archive_hash = digest(archive.read_bytes())
    checksum_path = archive.with_suffix(archive.suffix + ".sha256")
    checksum_path.write_text(f"{archive_hash}  {archive.name}\n", encoding="utf-8")
    build_info_path = output / f"InkDesk_v{version}_build-info.json"
    build_info_path.write_text(json.dumps({**build_info, "archive": archive.name, "sha256": archive_hash, "members": len(members)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "sha256": archive_hash, "members": len(members), "commit": commit, "tag": tag}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
