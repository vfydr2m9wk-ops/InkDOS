#!/usr/bin/env python3
"""Transactional InkDOS updater with a repository-trusted control plane."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile

PRODUCT = "InkDOS"
STATE = "DEVELOPMENT_STATE.json"
VERSION = "VERSION.json"

MAX_ENTRIES = 10_000
MAX_SINGLE = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250

# Stable update ZIPs are data packages. They must never replace code/configuration
# that GitHub Actions or the updater itself trusts and executes.
CONTROL_PREFIXES = (".github/", "scripts/", "tests/")
CONTROL_FILES = frozenset(
    {
        "requirements-ci.txt",
        "pyproject.toml",
        "pytest.ini",
        "tox.ini",
        ".coveragerc",
    }
)


class UpdateError(RuntimeError):
    pass


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise UpdateError(f"Invalid JSON {path}: {exc}") from exc


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe(raw):
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise UpdateError(f"Unsafe path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise UpdateError(f"Unsafe path: {raw!r}")
    value = path.as_posix()
    folded = value.casefold()
    if folded == ".git" or folded.startswith(".git/"):
        raise UpdateError("Git metadata is protected")
    return path


def is_control_plane(raw):
    value = safe(raw).as_posix().casefold()
    if value in {item.casefold() for item in CONTROL_FILES}:
        return True
    return any(value.startswith(prefix.casefold()) for prefix in CONTROL_PREFIXES)


def safe_payload(raw):
    path = safe(raw)
    if is_control_plane(path.as_posix()):
        raise UpdateError(f"Trusted control-plane path is protected: {path.as_posix()}")
    return path


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise UpdateError("patch-manifest.json must contain an object")
    if manifest.get("product") != PRODUCT:
        raise UpdateError("Wrong product")
    if manifest.get("allowWorkflowChanges"):
        raise UpdateError("Workflow changes are forbidden")
    if manifest.get("allowControlPlaneChanges"):
        raise UpdateError("Control-plane changes are forbidden")
    if manifest.get("mode", "incremental") not in {"incremental", "full-snapshot"}:
        raise UpdateError(f"Unsupported update mode: {manifest.get('mode')}")
    if not isinstance(manifest.get("sequence"), int) or manifest["sequence"] < 1:
        raise UpdateError("Invalid package sequence")
    if not isinstance(manifest.get("packageLabel"), str) or not manifest["packageLabel"].strip():
        raise UpdateError("Invalid package label")
    profile = manifest.get("validationProfile", "full")
    if profile not in {"standard", "full"}:
        raise UpdateError("Package validationProfile must be standard or full")
    required = manifest.get("requires")
    if not isinstance(required, dict) or not isinstance(required.get("previousSequence"), int):
        raise UpdateError("Package requires.previousSequence is missing or invalid")
    declared = manifest.get("files")
    if not isinstance(declared, dict):
        raise UpdateError("Package files manifest is missing or invalid")
    for rel, metadata in declared.items():
        safe_payload(rel)
        if not isinstance(metadata, dict):
            raise UpdateError(f"Invalid manifest metadata for {rel}")
        expected = metadata.get("sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise UpdateError(f"Invalid SHA-256 declaration for {rel}")
        try:
            int(expected, 16)
        except ValueError as exc:
            raise UpdateError(f"Invalid SHA-256 declaration for {rel}") from exc


def inspect(package):
    total = 0
    seen = set()
    with zipfile.ZipFile(package) as archive:
        infos = archive.infolist()
        names = {item.filename for item in infos}
        if len(infos) > MAX_ENTRIES:
            raise UpdateError("Too many ZIP entries")
        if "patch-manifest.json" not in names:
            raise UpdateError("patch-manifest.json is required")
        for info in infos:
            raw = info.filename.rstrip("/")
            if not raw:
                continue
            path = safe(raw)
            value = path.as_posix()
            if value not in {"patch-manifest.json", "DELETE.txt"} and not value.startswith("files/"):
                raise UpdateError(f"Unexpected package entry: {value}")
            if value.startswith("files/"):
                inner = value[len("files/") :]
                if not inner:
                    continue
                safe_payload(inner)
            key = value.casefold()
            if key in seen:
                raise UpdateError(f"Duplicate/case-colliding path: {value}")
            seen.add(key)
            if info.flag_bits & 0x1:
                raise UpdateError(f"Encrypted ZIP entry is forbidden: {value}")
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise UpdateError(f"Symlink ZIP entry is forbidden: {value}")
            total += info.file_size
            if info.file_size > MAX_SINGLE or total > MAX_TOTAL:
                raise UpdateError("ZIP size limit exceeded")
            if (
                info.file_size > 1024
                and info.compress_size > 0
                and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO
            ):
                raise UpdateError(f"Suspicious ZIP compression ratio: {value}")


def extract(package, dest):
    with zipfile.ZipFile(package) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            raw = info.filename
            path = safe(raw)
            value = path.as_posix()
            if value.startswith("files/"):
                safe_payload(value[len("files/") :])
            target = dest.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def verify_payload(extracted, manifest):
    declared = manifest["files"]
    payload = extracted / "files"
    actual = {
        path.relative_to(payload).as_posix()
        for path in payload.rglob("*")
        if path.is_file()
    } if payload.is_dir() else set()
    if actual != set(declared):
        missing = sorted(set(declared) - actual)
        extra = sorted(actual - set(declared))
        raise UpdateError(
            f"Payload file-set mismatch; missing={missing[:5]} extra={extra[:5]}"
        )
    for rel, metadata in declared.items():
        safe_payload(rel)
        got = sha(payload / rel)
        if got.lower() != metadata["sha256"].lower():
            raise UpdateError(f"Payload SHA-256 mismatch: {rel}")


def validate_base(repo, manifest):
    state = load(repo / STATE)
    version = load(repo / VERSION)
    required = manifest["requires"]
    if state.get("appliedSequence") != required["previousSequence"]:
        raise UpdateError(f"Base sequence mismatch: {state.get('appliedSequence')}")
    if manifest["sequence"] != state.get("appliedSequence", 0) + 1:
        raise UpdateError("Package sequence is not next")
    allowed = required.get("appVersions") or []
    if allowed and version.get("version") not in allowed:
        raise UpdateError(f"Base version not allowed: {version.get('version')}")


def copy_control_plane(repo, candidate):
    for prefix in CONTROL_PREFIXES:
        rel = prefix.rstrip("/")
        source = repo / rel
        if not source.exists():
            continue
        target = candidate / rel
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for rel in CONTROL_FILES:
        source = repo / rel
        if source.is_file():
            target = candidate / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def overlay(payload, candidate):
    if not payload.is_dir():
        return
    for source in sorted(payload.rglob("*")):
        if not source.is_file():
            continue
        rel = source.relative_to(payload).as_posix()
        safe_payload(rel)
        target = candidate / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def write_state(candidate, manifest):
    (candidate / STATE).write_text(
        json.dumps(
            {
                "schemaVersion": 2,
                "appliedSequence": manifest["sequence"],
                "currentPackage": manifest["packageLabel"],
                "status": "complete",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def ignore_copy(directory, names):
    ignored = {
        name
        for name in names
        if name in {".git", "__pycache__", ".venv", "node_modules", "test-results"}
        or (name.startswith("InkDOS-update-v") and name.endswith(".zip"))
    }
    return ignored


def build(repo, extracted, candidate, manifest):
    mode = manifest.get("mode", "incremental")
    payload = extracted / "files"
    if mode == "full-snapshot":
        copy_control_plane(repo, candidate)
        overlay(payload, candidate)
    elif mode == "incremental":
        shutil.copytree(
            repo,
            candidate,
            dirs_exist_ok=True,
            ignore=ignore_copy,
        )
        overlay(payload, candidate)
        delete_file = extracted / "DELETE.txt"
        if delete_file.is_file():
            for line in delete_file.read_text(encoding="utf-8").splitlines():
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                rel = safe_payload(raw)
                target = candidate.joinpath(*rel.parts)
                if target.is_dir():
                    shutil.rmtree(target)
                elif target.exists():
                    target.unlink()
    else:
        raise UpdateError(f"Unsupported update mode: {mode}")
    write_state(candidate, manifest)


def fmap(root):
    root = Path(root)
    result = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if (
            rel.startswith(".git/")
            or "__pycache__/" in rel
            or rel.startswith(".venv/")
            or rel.startswith("node_modules/")
            or (path.name.startswith("InkDOS-update-v") and path.suffix == ".zip")
        ):
            continue
        result[rel] = sha(path)
    return result


def control_map(root):
    return {
        rel: digest
        for rel, digest in fmap(root).items()
        if is_control_plane(rel)
    }


def ensure_control_identity(repo, candidate):
    if control_map(repo) != control_map(candidate):
        raise UpdateError("Candidate changed trusted control-plane files")


def run_validation(candidate, profile):
    if profile == "none":
        return
    python = sys.executable
    command = (
        [python, "scripts/run_release_validation.py"]
        if profile == "full"
        else [python, "scripts/validate_repository.py"]
    )
    subprocess.run(command, cwd=candidate, check=True)


def apply_diff(repo, candidate):
    before = fmap(repo)
    after = fmap(candidate)
    changed = sorted(rel for rel, digest in after.items() if before.get(rel) != digest)
    deleted = sorted(rel for rel in before if rel not in after)
    for rel in changed + deleted:
        if is_control_plane(rel):
            raise UpdateError(f"Control-plane mutation refused: {rel}")

    touched = sorted(set(changed + deleted))
    with tempfile.TemporaryDirectory(prefix="inkdos-rollback-") as temp_name:
        backup = Path(temp_name)
        snapshots = {}
        try:
            for rel in touched:
                path = repo / rel
                if path.is_file():
                    copy = backup / rel
                    copy.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, copy)
                    snapshots[rel] = copy
                else:
                    snapshots[rel] = None
            for rel in deleted:
                path = repo / rel
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
            for rel in changed:
                source = candidate / rel
                target = repo / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

            directories = sorted(
                (path for path in repo.rglob("*") if path.is_dir()),
                key=lambda item: len(item.parts),
                reverse=True,
            )
            for directory in directories:
                rel = directory.relative_to(repo).as_posix()
                if (
                    rel == ".git"
                    or rel.startswith(".git/")
                    or is_control_plane(rel + "/placeholder")
                ):
                    continue
                try:
                    directory.rmdir()
                except OSError:
                    pass
        except Exception:
            for rel in touched:
                path = repo / rel
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                snapshot = snapshots[rel]
                if snapshot is not None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(snapshot, path)
            raise
    return (
        [rel for rel in changed if rel not in before],
        [rel for rel in changed if rel in before],
        deleted,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--validation-profile",
        choices=["none", "standard", "full"],
    )
    args = parser.parse_args()

    package = Path(args.package).resolve()
    repo = Path(args.repo).resolve()
    report = Path(args.report)
    result = {"status": "failed"}

    try:
        inspect(package)
        with tempfile.TemporaryDirectory(prefix="inkdos-extract-") as extracted_name, tempfile.TemporaryDirectory(prefix="inkdos-candidate-") as candidate_name:
            extracted = Path(extracted_name)
            candidate = Path(candidate_name)
            extract(package, extracted)
            manifest = load(extracted / "patch-manifest.json")
            validate_manifest(manifest)
            validate_base(repo, manifest)
            verify_payload(extracted, manifest)
            build(repo, extracted, candidate, manifest)
            ensure_control_identity(repo, candidate)

            profile = args.validation_profile or manifest.get("validationProfile", "full")
            run_validation(candidate, profile)
            if args.dry_run:
                added = replaced = deleted = []
                status = "validated"
            else:
                added, replaced, deleted = apply_diff(repo, candidate)
                status = "applied"

            result.update(
                {
                    "status": status,
                    "packageLabel": manifest["packageLabel"],
                    "targetRelease": manifest.get("targetRelease"),
                    "sequence": manifest["sequence"],
                    "validationProfile": profile,
                    "mode": manifest.get("mode", "incremental"),
                    "copied": added + replaced,
                    "added": added,
                    "replaced": replaced,
                    "deleted": deleted,
                }
            )
    except Exception as exc:
        result["error"] = str(exc)
        report.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Update failed: {exc}", file=sys.stderr)
        raise

    report.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
