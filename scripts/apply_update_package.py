#!/usr/bin/env python3
"""Safely apply an incremental InkDesk update package.

The package format is intentionally small:

    patch-manifest.json
    files/<repository-relative files>
    DELETE.txt                     # optional

The updater validates paths, sequence order, archive limits, and the base
version before changing the repository. Changes are transactional: existing
files are backed up and restored when validation fails.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile

SCHEMA_VERSION = 1
PRODUCT = "InkDesk"
STATE_FILE = "DEVELOPMENT_STATE.json"
VERSION_FILE = "VERSION.json"
MAX_ENTRIES = 10_000
MAX_TOTAL_UNCOMPRESSED = 512 * 1024 * 1024
MAX_SINGLE_FILE = 128 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250
PROTECTED_PREFIXES = (".git/",)
WORKFLOW_PREFIX = ".github/workflows/"

VALIDATION_PROFILES: dict[str, list[list[str]]] = {
    "none": [],
    "standard": [
        [sys.executable, "scripts/generate_release_metadata.py"],
        [sys.executable, "scripts/check_no_legacy_runtime.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        [sys.executable, "scripts/validate_repository.py"],
        [sys.executable, "scripts/audit_source.py"],
    ],
    "full": [
        [sys.executable, "scripts/generate_release_metadata.py"],
        [sys.executable, "scripts/check_no_legacy_runtime.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        [sys.executable, "scripts/validate_repository.py"],
        [sys.executable, "scripts/audit_source.py"],
        [sys.executable, "scripts/run_release_validation.py"],
    ],
}


class UpdateError(RuntimeError):
    """Controlled update-package failure."""


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise UpdateError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise UpdateError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise UpdateError(f"Expected a JSON object in {path}")
    return value


def safe_relative_path(raw: str, *, allow_directory: bool = False) -> PurePosixPath:
    if not isinstance(raw, str) or not raw.strip():
        raise UpdateError("Package paths must be non-empty strings")
    if "\\" in raw:
        raise UpdateError(f"Backslashes are not allowed in package paths: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute():
        raise UpdateError(f"Absolute paths are not allowed: {raw!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise UpdateError(f"Unsafe or non-normalized path: {raw!r}")
    normalized = path.as_posix()
    if normalized == ".git" or normalized.startswith(PROTECTED_PREFIXES):
        raise UpdateError(f"Protected Git path is not allowed: {raw!r}")
    if not allow_directory and raw.endswith("/"):
        raise UpdateError(f"Expected a file path, got a directory: {raw!r}")
    return path


def validate_zip_info(info: zipfile.ZipInfo) -> None:
    name = info.filename
    safe_relative_path(name.rstrip("/"), allow_directory=True)
    # Unix symlinks are identified by the file type bits in external_attr.
    file_type = (info.external_attr >> 16) & 0o170000
    if file_type == 0o120000:
        raise UpdateError(f"Symbolic links are not allowed in update packages: {name}")
    if info.file_size > MAX_SINGLE_FILE:
        raise UpdateError(f"Package member exceeds the per-file limit: {name}")
    if info.compress_size == 0:
        ratio = float("inf") if info.file_size else 1.0
    else:
        ratio = info.file_size / info.compress_size
    if ratio > MAX_COMPRESSION_RATIO:
        raise UpdateError(f"Suspicious compression ratio for package member: {name}")


def inspect_archive(zf: zipfile.ZipFile) -> None:
    infos = zf.infolist()
    if len(infos) > MAX_ENTRIES:
        raise UpdateError(f"Package contains too many entries: {len(infos)}")
    seen: set[str] = set()
    total = 0
    for info in infos:
        validate_zip_info(info)
        key = info.filename.rstrip("/")
        folded = key.casefold()
        if folded in seen:
            raise UpdateError(f"Duplicate or case-colliding package path: {info.filename}")
        seen.add(folded)
        total += info.file_size
        if total > MAX_TOTAL_UNCOMPRESSED:
            raise UpdateError("Package exceeds the total uncompressed-size limit")


def extract_package(package: Path, destination: Path) -> None:
    try:
        with zipfile.ZipFile(package) as zf:
            inspect_archive(zf)
            for info in zf.infolist():
                if info.is_dir():
                    continue
                rel = safe_relative_path(info.filename)
                target = destination.joinpath(*rel.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info, "r") as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    except zipfile.BadZipFile as exc:
        raise UpdateError(f"Invalid ZIP package: {package}") from exc


def validate_manifest(manifest: dict) -> None:
    required = {
        "schemaVersion",
        "product",
        "targetRelease",
        "packageLabel",
        "sequence",
        "requires",
        "description",
        "validationProfile",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise UpdateError(f"Patch manifest is missing fields: {', '.join(missing)}")
    if manifest["schemaVersion"] != SCHEMA_VERSION:
        raise UpdateError(f"Unsupported patch schema: {manifest['schemaVersion']}")
    if manifest["product"] != PRODUCT:
        raise UpdateError(f"This package targets {manifest['product']!r}, not {PRODUCT!r}")
    if not isinstance(manifest["sequence"], int) or manifest["sequence"] < 1:
        raise UpdateError("Patch sequence must be a positive integer")
    if not isinstance(manifest["requires"], dict):
        raise UpdateError("Patch manifest requires must be an object")
    if manifest["validationProfile"] not in VALIDATION_PROFILES:
        raise UpdateError(f"Unknown validation profile: {manifest['validationProfile']}")


def current_app_version(repo: Path) -> str:
    return str(load_json(repo / VERSION_FILE).get("version", ""))


def validate_sequence(repo: Path, manifest: dict) -> None:
    requirements = manifest["requires"]
    expected_previous = requirements.get("previousSequence")
    allowed_versions = requirements.get("appVersions", [])
    state_path = repo / STATE_FILE
    if state_path.exists():
        state = load_json(state_path)
        if state.get("targetRelease") != manifest["targetRelease"]:
            raise UpdateError(
                f"Repository is tracking {state.get('targetRelease')!r}, "
                f"but this package targets {manifest['targetRelease']!r}"
            )
        actual_previous = state.get("appliedSequence", 0)
    else:
        actual_previous = 0
    if expected_previous is not None and actual_previous != expected_previous:
        raise UpdateError(
            f"Patch order mismatch: expected previous sequence {expected_previous}, "
            f"repository reports {actual_previous}"
        )
    if manifest["sequence"] != actual_previous + 1:
        raise UpdateError(
            f"Patch sequence {manifest['sequence']} is not the next sequence after {actual_previous}"
        )
    app_version = current_app_version(repo)
    if allowed_versions and app_version not in allowed_versions:
        raise UpdateError(
            f"Base application version {app_version!r} is not supported by this package; "
            f"allowed: {', '.join(map(str, allowed_versions))}"
        )


def parse_delete_list(path: Path) -> list[PurePosixPath]:
    if not path.exists():
        return []
    result: list[PurePosixPath] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        try:
            result.append(safe_relative_path(value, allow_directory=True))
        except UpdateError as exc:
            raise UpdateError(f"DELETE.txt line {line_number}: {exc}") from exc
    return result


def iter_payload_files(payload_root: Path) -> list[tuple[Path, PurePosixPath]]:
    if not payload_root.is_dir():
        raise UpdateError("Update package does not contain a files/ directory")
    files: list[tuple[Path, PurePosixPath]] = []
    folded: set[str] = set()
    for source in sorted(payload_root.rglob("*")):
        if not source.is_file():
            continue
        rel = PurePosixPath(source.relative_to(payload_root).as_posix())
        safe_relative_path(rel.as_posix())
        key = rel.as_posix().casefold()
        if key in folded:
            raise UpdateError(f"Payload contains a case-colliding path: {rel}")
        folded.add(key)
        files.append((source, rel))
    if not files:
        raise UpdateError("Update package files/ directory is empty")
    return files


def validate_workflow_changes(
    payload: list[tuple[Path, PurePosixPath]],
    deletions: list[PurePosixPath],
) -> None:
    workflow_paths = [
        rel.as_posix()
        for _, rel in payload
        if rel.as_posix().startswith(WORKFLOW_PREFIX)
    ] + [
        rel.as_posix()
        for rel in deletions
        if rel.as_posix().startswith(WORKFLOW_PREFIX)
    ]
    if workflow_paths:
        raise UpdateError(
            "Stable update packages cannot create, modify, or delete GitHub "
            "workflow files. Install workflow changes manually as a one-time "
            "bootstrap, then keep update ZIPs workflow-free. Offending paths: "
            + ", ".join(sorted(workflow_paths))
        )


def ensure_within_repo(repo: Path, rel: PurePosixPath) -> Path:
    target = repo.joinpath(*rel.parts)
    resolved_parent = target.parent.resolve()
    repo_resolved = repo.resolve()
    try:
        resolved_parent.relative_to(repo_resolved)
    except ValueError as exc:
        raise UpdateError(f"Target escapes the repository: {rel}") from exc
    return target


def build_state(manifest: dict, prior_state: dict | None) -> dict:
    history = list((prior_state or {}).get("history", []))
    history.append(
        {
            "sequence": manifest["sequence"],
            "packageLabel": manifest["packageLabel"],
            "description": manifest["description"],
        }
    )
    return {
        "schemaVersion": 1,
        "targetRelease": manifest["targetRelease"],
        "baseVersion": (prior_state or {}).get("baseVersion"),
        "appliedSequence": manifest["sequence"],
        "currentPackage": manifest["packageLabel"],
        "status": "in-progress",
        "history": history,
    }


def run_validation(repo: Path, profile: str) -> None:
    for command in VALIDATION_PROFILES[profile]:
        printable = " ".join(command)
        print(f"::group::Validation: {printable}")
        try:
            subprocess.run(command, cwd=repo, check=True)
        finally:
            print("::endgroup::")


def apply_transaction(
    repo: Path,
    payload: list[tuple[Path, PurePosixPath]],
    deletions: list[PurePosixPath],
    manifest: dict,
    *,
    dry_run: bool,
) -> dict:
    add_or_replace = {rel.as_posix(): (source, rel) for source, rel in payload}
    delete_set = {rel.as_posix(): rel for rel in deletions}
    overlap = sorted(set(add_or_replace) & set(delete_set))
    if overlap:
        raise UpdateError(f"Paths cannot be both copied and deleted: {', '.join(overlap)}")

    prior_state = load_json(repo / STATE_FILE) if (repo / STATE_FILE).exists() else None
    state = build_state(manifest, prior_state)
    if not state["baseVersion"]:
        state["baseVersion"] = current_app_version(repo)

    plan = {
        "packageLabel": manifest["packageLabel"],
        "targetRelease": manifest["targetRelease"],
        "sequence": manifest["sequence"],
        "copied": sorted(add_or_replace),
        "deleted": sorted(delete_set),
        "validationProfile": manifest["validationProfile"],
        "dryRun": dry_run,
        "status": "dry-run" if dry_run else "pending",
        "rollback": False,
        "workflowObservation": manifest.get("workflowObservation", ""),
    }
    if dry_run:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return plan

    with tempfile.TemporaryDirectory(prefix="inkdesk-update-backup-") as backup_name:
        backup = Path(backup_name)
        touched: list[tuple[Path, Path | None]] = []
        try:
            for rel_text in sorted(set(add_or_replace) | set(delete_set) | {STATE_FILE}):
                rel = safe_relative_path(rel_text, allow_directory=True)
                target = ensure_within_repo(repo, rel)
                if target.exists():
                    backup_target = backup.joinpath(*rel.parts)
                    backup_target.parent.mkdir(parents=True, exist_ok=True)
                    if target.is_dir():
                        shutil.copytree(target, backup_target)
                    else:
                        shutil.copy2(target, backup_target)
                    touched.append((target, backup_target))
                else:
                    touched.append((target, None))

            # Deletions are intentionally processed before copies.
            for rel in deletions:
                target = ensure_within_repo(repo, rel)
                if target.is_dir():
                    shutil.rmtree(target)
                elif target.exists():
                    target.unlink()

            for source, rel in payload:
                target = ensure_within_repo(repo, rel)
                if target.exists() and target.is_dir():
                    shutil.rmtree(target)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

            (repo / STATE_FILE).write_text(
                json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            run_validation(repo, manifest["validationProfile"])
        except Exception:
            print("Update failed; restoring repository files.", file=sys.stderr)
            for target, backup_target in reversed(touched):
                if target.is_dir():
                    shutil.rmtree(target)
                elif target.exists():
                    target.unlink()
                if backup_target is not None:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if backup_target.is_dir():
                        shutil.copytree(backup_target, target)
                    else:
                        shutil.copy2(backup_target, target)
            raise

    plan["status"] = "applied"
    return plan


def package_manifest_summary(package: Path) -> dict:
    try:
        with zipfile.ZipFile(package) as archive:
            value = json.loads(archive.read("patch-manifest.json").decode("utf-8"))
            return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_failure_report(path: Path, package: Path, repo: Path, error: Exception) -> None:
    manifest = package_manifest_summary(package)
    prior_state = {}
    try:
        state_path = repo / STATE_FILE
        if state_path.exists():
            prior_state = load_json(state_path)
    except Exception:
        prior_state = {}
    report = {
        "status": "failed",
        "rollback": True,
        "error": str(error),
        "packageLabel": manifest.get("packageLabel", package.name),
        "targetRelease": manifest.get("targetRelease", ""),
        "sequence": manifest.get("sequence"),
        "validationProfile": manifest.get("validationProfile", ""),
        "dryRun": False,
        "copied": [],
        "deleted": [],
        "workflowObservation": manifest.get("workflowObservation", ""),
        "repositorySequenceAfterRollback": prior_state.get("appliedSequence", 0),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_package(
    package: Path,
    repo: Path,
    *,
    dry_run: bool = False,
    validation_override: str | None = None,
) -> dict:
    package = package.resolve()
    repo = repo.resolve()
    if not package.is_file():
        raise UpdateError(f"Update package not found: {package}")
    if not (repo / VERSION_FILE).is_file():
        raise UpdateError(f"Not an InkDesk repository: {repo}")

    with tempfile.TemporaryDirectory(prefix="inkdesk-update-stage-") as stage_name:
        stage = Path(stage_name)
        extract_package(package, stage)
        manifest = load_json(stage / "patch-manifest.json")
        validate_manifest(manifest)
        if validation_override is not None:
            if validation_override not in VALIDATION_PROFILES:
                raise UpdateError(f"Unknown validation override: {validation_override}")
            manifest["validationProfile"] = validation_override
        validate_sequence(repo, manifest)
        payload = iter_payload_files(stage / "files")
        deletions = parse_delete_list(stage / "DELETE.txt")
        validate_workflow_changes(payload, deletions)
        return apply_transaction(repo, payload, deletions, manifest, dry_run=dry_run)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path, help="Update ZIP package")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the plan only")
    parser.add_argument(
        "--validation-profile",
        choices=sorted(VALIDATION_PROFILES),
        help="Override the package validation profile",
    )
    parser.add_argument("--report", type=Path, help="Write the applied plan as JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        plan = apply_package(
            args.package,
            args.repo,
            dry_run=args.dry_run,
            validation_override=args.validation_profile,
        )
    except (UpdateError, subprocess.CalledProcessError, OSError) as exc:
        if args.report:
            try:
                write_failure_report(args.report, args.package.resolve(), args.repo.resolve(), exc)
            except Exception as report_error:
                print(f"WARNING: could not write failure report: {report_error}", file=sys.stderr)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: applied InkDesk update package {plan['packageLabel']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
