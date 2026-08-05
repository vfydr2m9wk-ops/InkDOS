#!/usr/bin/env python3
"""Build a deterministic InkDesk runtime ZIP from a clean, tagged Git checkout."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
FIXED_TIMESTAMP = "1980-01-01T00:00:00Z"
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


class BuildError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise BuildError("Git is required for an official InkDesk build.") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "Git command failed.").strip()
        raise BuildError(detail) from error
    return completed.stdout.strip()


def verify_git_checkout(version: str) -> tuple[str, str]:
    top_level = Path(git("rev-parse", "--show-toplevel")).resolve()
    if top_level != ROOT.resolve():
        raise BuildError(f"Build root does not match the Git checkout: {top_level}")

    status = git("status", "--porcelain=v1", "--untracked-files=all")
    if status:
        changed = ", ".join(line[3:] for line in status.splitlines()[:10])
        raise BuildError(f"Official builds require a clean working tree. Changed paths: {changed}")

    commit = git("rev-parse", "HEAD")
    tag = f"v{version}"
    try:
        tag_commit = git("rev-list", "-n", "1", tag)
    except BuildError as error:
        raise BuildError(f"Required tag {tag} does not exist in this checkout.") from error
    if tag_commit != commit:
        raise BuildError(f"Required tag {tag} does not point to HEAD ({commit}).")

    tags_at_head = set(git("tag", "--points-at", "HEAD").splitlines())
    if tag not in tags_at_head:
        raise BuildError(f"HEAD is not tagged with {tag}.")
    return commit, tag


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


def dependency_metadata() -> list[dict[str, str]]:
    return [
        {
            "name": "JSZip",
            "version": "3.10.1",
            "license": "MIT OR GPL-3.0-only",
            "source": "https://github.com/Stuk/jszip",
            "path": "shared/vendor/jszip.min.js",
            "purpose": "Read and write ZIP-based OOXML packages",
        },
        {
            "name": "pako",
            "version": "1.0.11",
            "license": "MIT",
            "source": "https://github.com/nodeca/pako",
            "path": "shared/vendor/pako_inflate.min.js",
            "purpose": "Raw DEFLATE support for compatibility parsing",
        },
    ]


def create_sbom(version: str, commit: str, source_members: dict[str, bytes]) -> bytes:
    project_id = "SPDXRef-Package-InkDesk"
    packages = [
        {
            "name": "InkDesk",
            "SPDXID": project_id,
            "versionInfo": version,
            "downloadLocation": "https://github.com/vfydr2m9wk-ops/InkDesk",
            "filesAnalyzed": False,
            "licenseConcluded": "MIT",
            "licenseDeclared": "MIT",
            "copyrightText": "NOASSERTION",
        }
    ]
    relationships = [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": project_id}]

    for index, dependency in enumerate(dependency_metadata(), start=1):
        data = source_members[dependency["path"]]
        package_id = f"SPDXRef-Package-Dependency-{index}"
        packages.append(
            {
                "name": dependency["name"],
                "SPDXID": package_id,
                "versionInfo": dependency["version"],
                "downloadLocation": dependency["source"],
                "filesAnalyzed": False,
                "licenseConcluded": dependency["license"],
                "licenseDeclared": dependency["license"],
                "copyrightText": "NOASSERTION",
                "checksums": [{"algorithm": "SHA256", "checksumValue": digest(data)}],
                "comment": f"Vendored locally at {dependency['path']}; purpose: {dependency['purpose']}; modified: no documented modification.",
            }
        )
        relationships.append({"spdxElementId": project_id, "relationshipType": "DEPENDS_ON", "relatedSpdxElement": package_id})

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"InkDesk-{version}-SBOM",
        "documentNamespace": f"https://github.com/vfydr2m9wk-ops/InkDesk/spdx/{commit}",
        "creationInfo": {"created": FIXED_TIMESTAMP, "creators": ["Tool: InkDesk deterministic release builder"]},
        "packages": packages,
        "relationships": relationships,
    }
    return (json.dumps(sbom, indent=2, sort_keys=True) + "\n").encode()


def render_archive(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=True) as package:
        for name, data in sorted(members.items()):
            package.writestr(zip_info(name), data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="dist")
    args = parser.parse_args()

    try:
        version_doc = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        version = str(version_doc["version"])
        commit, tag = verify_git_checkout(version)

        output = (ROOT / args.output_dir).resolve()
        output.mkdir(parents=True, exist_ok=True)
        archive = output / f"InkDesk_v{version}.zip"

        source_members: dict[str, bytes] = {}
        for path in included_paths():
            source_members[path.relative_to(ROOT).as_posix()] = path.read_bytes()

        members = dict(source_members)
        members["SBOM.spdx.json"] = create_sbom(version, commit, source_members)
        source_manifest = {
            "schemaVersion": 1,
            "project": "InkDesk",
            "version": version,
            "commit": commit,
            "tag": tag,
            "files": [
                {"path": name, "size": len(data), "sha256": digest(data)}
                for name, data in sorted(members.items())
            ],
        }
        members["SOURCE_MANIFEST.json"] = (json.dumps(source_manifest, indent=2, sort_keys=True) + "\n").encode()

        build_info = {
            "project": "InkDesk",
            "version": version,
            "releaseChannel": version_doc.get("releaseChannel", "beta"),
            "tag": tag,
            "commit": commit,
            "sourceRepository": version_doc.get("repository"),
            "gitTreeClean": True,
            "tagMatchesHead": True,
            "reproducibleArchive": True,
            "reproducibilityCheck": "two in-process builds compared byte-for-byte",
            "archiveTimestamp": FIXED_TIMESTAMP,
        }
        members["BUILD_INFO.json"] = (json.dumps(build_info, indent=2, sort_keys=True) + "\n").encode()
        runtime_checksums = "".join(f"{digest(data)}  {name}\n" for name, data in sorted(members.items()))
        members["RUNTIME_CHECKSUMS.sha256"] = runtime_checksums.encode()

        first_build = render_archive(members)
        second_build = render_archive(members)
        if first_build != second_build:
            raise BuildError("Deterministic build verification failed: the two archives differ.")
        archive.write_bytes(first_build)

        archive_hash = digest(first_build)
        checksum_path = archive.with_suffix(archive.suffix + ".sha256")
        checksum_path.write_text(f"{archive_hash}  {archive.name}\n", encoding="utf-8")
        build_info_path = output / f"InkDesk_v{version}_build-info.json"
        build_info_path.write_text(
            json.dumps({**build_info, "archive": archive.name, "sha256": archive_hash, "members": len(members)}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"archive": str(archive), "sha256": archive_hash, "members": len(members), "commit": commit, "tag": tag}, indent=2))
        return 0
    except (BuildError, KeyError, json.JSONDecodeError) as error:
        print(f"Release build refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
