#!/usr/bin/env python3
"""Apply a validated InkDOS update to a disposable candidate, then commit its diff.

Package format (schema 2):

    patch-manifest.json
    files/<repository-relative files>
    DELETE.txt                     # optional

The manifest may also declare tree-wide text replacements, file merges and path
moves. All operations run only inside a disposable repository candidate before
validation. Git metadata and GitHub workflow files are permanently protected.
Stable update packages cannot create, modify, or delete GitHub workflow files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile

SCHEMA_VERSION = 2
PRODUCT = "InkDOS"
STATE_FILE = "DEVELOPMENT_STATE.json"
VERSION_FILE = "VERSION.json"
WORKFLOW_PREFIX = ".github/workflows/"
MAX_ENTRIES = 10_000
MAX_TOTAL_UNCOMPRESSED = 512 * 1024 * 1024
MAX_SINGLE_FILE = 128 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250
IGNORED_PARTS = {
    ".git", "__pycache__", ".mobile-import", "_site", "test-results",
    "node_modules", ".venv", "dist",
}
TEXT_EXTENSIONS = {
    ".html", ".css", ".js", ".json", ".md", ".py", ".txt", ".cff",
    ".yml", ".yaml", ".webmanifest",
}

VALIDATION_PROFILES: dict[str, list[list[str]]] = {
    "none": [],
    "standard": [
        [sys.executable, "scripts/check_no_legacy_runtime.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        [sys.executable, "scripts/validate_repository.py"],
        [sys.executable, "scripts/audit_source.py"],
        [sys.executable, "scripts/check_architecture_guardrails.py"],
    ],
    "full": [
        [sys.executable, "scripts/check_no_legacy_runtime.py"],
        [sys.executable, "scripts/run_release_validation.py"],
    ],
}


class UpdateError(RuntimeError):
    pass


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_relative_path(raw: str, *, allow_directory: bool = False) -> PurePosixPath:
    if not isinstance(raw, str) or not raw.strip():
        raise UpdateError("Package paths must be non-empty strings")
    if "\\" in raw:
        raise UpdateError(f"Backslashes are not allowed in package paths: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise UpdateError(f"Unsafe or non-normalized path: {raw!r}")
    normalized = path.as_posix()
    if normalized == ".git" or normalized.startswith(".git/"):
        raise UpdateError(f"Protected Git path is not allowed: {raw!r}")
    if normalized == ".github/workflows" or normalized.startswith(WORKFLOW_PREFIX):
        raise UpdateError(
            f"Update packages cannot create, modify, or delete GitHub workflow files: {raw!r}"
        )
    if not allow_directory and raw.endswith("/"):
        raise UpdateError(f"Expected a file path, got a directory: {raw!r}")
    return path


def repo_target(repo: Path, rel: PurePosixPath) -> Path:
    target = repo.joinpath(*rel.parts)
    root = repo.resolve()
    try:
        target.parent.resolve().relative_to(root)
    except ValueError as exc:
        raise UpdateError(f"Target escapes repository: {rel}") from exc
    return target


def validate_zip_info(info: zipfile.ZipInfo) -> None:
    raw = info.filename.rstrip("/")
    if raw:
        path = PurePosixPath(raw)
        if "\\" in raw or path.is_absolute() or any(p in {"", ".", ".."} for p in path.parts):
            raise UpdateError(f"Unsafe ZIP path: {info.filename}")
    if ((info.external_attr >> 16) & 0o170000) == 0o120000:
        raise UpdateError(f"Symbolic links are not allowed: {info.filename}")
    if info.file_size > MAX_SINGLE_FILE:
        raise UpdateError(f"Package member exceeds per-file size limit: {info.filename}")
    ratio = info.file_size / info.compress_size if info.compress_size else (float("inf") if info.file_size else 1)
    if ratio > MAX_COMPRESSION_RATIO:
        raise UpdateError(f"Suspicious compression ratio: {info.filename}")


def inspect_archive(zf: zipfile.ZipFile) -> None:
    infos = zf.infolist()
    if len(infos) > MAX_ENTRIES:
        raise UpdateError(f"Update ZIP has too many entries: {len(infos)}")
    seen: set[str] = set()
    total = 0
    for info in infos:
        validate_zip_info(info)
        key = info.filename.rstrip("/").casefold()
        if key and key in seen:
            raise UpdateError(f"Duplicate or case-colliding ZIP path: {info.filename}")
        if key:
            seen.add(key)
        total += info.file_size
        if total > MAX_TOTAL_UNCOMPRESSED:
            raise UpdateError("Update ZIP exceeds total uncompressed-size limit")


def extract_package(package: Path, destination: Path) -> None:
    try:
        with zipfile.ZipFile(package) as archive:
            inspect_archive(archive)
            for info in archive.infolist():
                if info.is_dir():
                    continue
                target = destination.joinpath(*PurePosixPath(info.filename).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile as exc:
        raise UpdateError(f"Invalid ZIP package: {package}") from exc


def validate_manifest(manifest: dict) -> None:
    required = {
        "schemaVersion", "product", "packageLabel", "sequence", "requires",
        "description", "validationProfile",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise UpdateError(f"Patch manifest is missing fields: {', '.join(missing)}")
    if manifest["schemaVersion"] != SCHEMA_VERSION:
        raise UpdateError(f"Unsupported patch schema: {manifest['schemaVersion']}")
    if manifest["product"] != PRODUCT:
        raise UpdateError(f"This package targets {manifest['product']!r}, not {PRODUCT!r}")
    if manifest.get("allowWorkflowChanges"):
        raise UpdateError("allowWorkflowChanges is forbidden in stable update packages")
    if not isinstance(manifest["sequence"], int) or manifest["sequence"] < 1:
        raise UpdateError("Patch sequence must be a positive integer")
    if not isinstance(manifest["requires"], dict):
        raise UpdateError("Patch manifest requires must be an object")
    if manifest["validationProfile"] not in VALIDATION_PROFILES:
        raise UpdateError(f"Unknown validation profile: {manifest['validationProfile']}")
    for field in ("files", "deletions", "textReplacements"):
        if field in manifest and not isinstance(manifest[field], dict):
            raise UpdateError(f"Manifest field {field!r} must be an object")
    operations = manifest.get("operations", {})
    if not isinstance(operations, dict):
        raise UpdateError("Manifest operations must be an object")
    for field, kind in (("treeReplacements", list), ("fileMerges", list), ("moves", dict)):
        if field in operations and not isinstance(operations[field], kind):
            raise UpdateError(f"operations.{field} has the wrong type")


def current_app_version(repo: Path) -> str:
    return str(load_json(repo / VERSION_FILE).get("version", ""))


def validate_sequence(repo: Path, manifest: dict) -> None:
    requirements = manifest["requires"]
    state = load_json(repo / STATE_FILE) if (repo / STATE_FILE).exists() else {}
    actual_previous = state.get("appliedSequence", 0)
    expected_previous = requirements.get("previousSequence")
    if expected_previous is not None and actual_previous != expected_previous:
        raise UpdateError(
            f"Patch order mismatch: expected previous sequence {expected_previous}, "
            f"repository reports {actual_previous}"
        )
    if manifest["sequence"] != actual_previous + 1:
        raise UpdateError(f"Patch sequence {manifest['sequence']} is not next after {actual_previous}")
    allowed_versions = requirements.get("appVersions", [])
    version = current_app_version(repo)
    if allowed_versions and version not in allowed_versions:
        raise UpdateError(
            f"Base application version {version!r} is not supported; allowed: "
            + ", ".join(map(str, allowed_versions))
        )


def parse_delete_list(path: Path) -> list[PurePosixPath]:
    if not path.exists():
        return []
    result: list[PurePosixPath] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        try:
            result.append(safe_relative_path(value, allow_directory=True))
        except UpdateError as exc:
            raise UpdateError(f"DELETE.txt line {number}: {exc}") from exc
    return result


def iter_payload_files(payload_root: Path) -> list[tuple[Path, PurePosixPath]]:
    if not payload_root.is_dir():
        raise UpdateError("Update package does not contain files/ directory")
    result: list[tuple[Path, PurePosixPath]] = []
    seen: set[str] = set()
    for source in sorted(payload_root.rglob("*")):
        if not source.is_file():
            continue
        rel = safe_relative_path(source.relative_to(payload_root).as_posix())
        key = rel.as_posix().casefold()
        if key in seen:
            raise UpdateError(f"Payload contains a case-colliding path: {rel}")
        seen.add(key)
        result.append((source, rel))
    if not result:
        raise UpdateError("Update package files/ directory is empty")
    return result


def verify_payload_contract(
    repo: Path,
    payload: list[tuple[Path, PurePosixPath]],
    deletions: list[PurePosixPath],
    manifest: dict,
) -> None:
    files = manifest.get("files", {})
    delete_contract = manifest.get("deletions", {})
    payload_names = {rel.as_posix() for _, rel in payload}
    deletion_names = {rel.as_posix() for rel in deletions}
    if files and set(files) != payload_names:
        raise UpdateError("Manifest files map does not exactly match files/ payload")
    if delete_contract and set(delete_contract) != deletion_names:
        raise UpdateError("Manifest deletions map does not exactly match DELETE.txt")
    overlap = sorted(payload_names & deletion_names)
    if overlap:
        raise UpdateError(f"Paths cannot be both copied and deleted: {', '.join(overlap)}")
    for source, rel in payload:
        meta = files.get(rel.as_posix(), {})
        expected = meta.get("sha256")
        if expected and sha256_file(source) != expected:
            raise UpdateError(f"Payload SHA-256 mismatch: {rel}")
        before = meta.get("beforeSha256")
        if before:
            target = repo_target(repo, rel)
            if not target.is_file() or sha256_file(target) != before:
                raise UpdateError(f"Base file SHA-256 mismatch: {rel}")


def should_ignore(rel: Path) -> bool:
    parts = rel.parts
    if any(part in IGNORED_PARTS for part in parts):
        return True
    return len(parts) >= 3 and parts[:2] == ("tests", "browser") and parts[2] == "results"


def copy_candidate(repo: Path, destination: Path) -> None:
    root = repo.resolve()
    def ignore(directory: str, names: list[str]) -> set[str]:
        current = Path(directory).resolve()
        try:
            rel = current.relative_to(root)
        except ValueError:
            rel = Path()
        ignored = {name for name in names if name in IGNORED_PARTS or name.endswith((".pyc", ".pyo"))}
        if rel.parts[:2] == ("tests", "browser") and "results" in names:
            ignored.add("results")
        return ignored
    shutil.copytree(repo, destination, ignore=ignore)


def overlay_payload(repo: Path, payload: list[tuple[Path, PurePosixPath]]) -> None:
    for source, rel in payload:
        target = repo_target(repo, rel)
        if target.exists() and target.is_dir():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def apply_file_merges(repo: Path, manifest: dict) -> dict[str, int]:
    metrics: dict[str, int] = {}
    for index, spec in enumerate(manifest.get("operations", {}).get("fileMerges", []), 1):
        if not isinstance(spec, dict):
            raise UpdateError(f"Invalid file merge #{index}")
        target_rel = safe_relative_path(spec.get("target", ""))
        raw_sources = spec.get("sources")
        if not isinstance(raw_sources, list) or len(raw_sources) < 2:
            raise UpdateError(f"fileMerges[{index}] requires at least two sources")
        sources = [safe_relative_path(item) for item in raw_sources]
        separator = spec.get("separator", "\n")
        if not isinstance(separator, str):
            raise UpdateError(f"fileMerges[{index}].separator must be a string")
        chunks: list[str] = []
        for rel in sources:
            path = repo_target(repo, rel)
            if not path.is_file():
                raise UpdateError(f"Merge source is missing: {rel}")
            chunks.append(path.read_text(encoding="utf-8").rstrip() + "\n")
        target = repo_target(repo, target_rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(separator.join(chunks), encoding="utf-8")
        metrics[target_rel.as_posix()] = len(sources)
        if spec.get("deleteSources", False):
            for rel in sources:
                source = repo_target(repo, rel)
                if source.resolve() != target.resolve() and source.exists():
                    source.unlink()
    return metrics


def iter_text_targets(repo: Path, spec: dict):
    extensions = spec.get("extensions", sorted(TEXT_EXTENSIONS))
    if not isinstance(extensions, list) or not extensions:
        raise UpdateError("treeReplacements extensions must be a non-empty array")
    normalized = {item if str(item).startswith(".") else "." + str(item) for item in extensions}
    excluded_prefixes = [safe_relative_path(value, allow_directory=True).as_posix().rstrip("/") for value in spec.get("excludePrefixes", [])]
    excluded_paths = {safe_relative_path(value, allow_directory=True).as_posix() for value in spec.get("excludePaths", [])}
    for path in sorted(repo.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(repo)
        text = rel.as_posix()
        if should_ignore(rel) or text.startswith(".github/") or "vendor" in rel.parts:
            continue
        if text in excluded_paths or any(text == prefix or text.startswith(prefix + "/") for prefix in excluded_prefixes):
            continue
        if path.suffix.lower() not in normalized:
            continue
        yield path, text


def apply_tree_replacements(repo: Path, manifest: dict) -> dict[str, int]:
    metrics: dict[str, int] = {}
    specs = manifest.get("operations", {}).get("treeReplacements", [])
    for index, spec in enumerate(specs, 1):
        if not isinstance(spec, dict):
            raise UpdateError(f"Invalid tree replacement #{index}")
        old, new = spec.get("old"), spec.get("new")
        if not isinstance(old, str) or not old or not isinstance(new, str):
            raise UpdateError(f"Invalid tree replacement #{index}")
        count = 0
        files = 0
        for path, _ in iter_text_targets(repo, spec):
            try:
                original = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            occurrences = original.count(old)
            if not occurrences:
                continue
            path.write_text(original.replace(old, new), encoding="utf-8")
            count += occurrences
            files += 1
        minimum = spec.get("minMatches", 1)
        maximum = spec.get("maxMatches")
        if not isinstance(minimum, int) or minimum < 0:
            raise UpdateError(f"Invalid minMatches in tree replacement #{index}")
        if count < minimum:
            raise UpdateError(
                f"Tree replacement #{index} base mismatch: expected at least {minimum}, found {count}"
            )
        if maximum is not None and (not isinstance(maximum, int) or count > maximum):
            raise UpdateError(
                f"Tree replacement #{index} exceeded maxMatches {maximum}: found {count}"
            )
        metrics[f"{old}->{new}"] = count
        print(f"Tree replacement {old!r} -> {new!r}: {count} occurrence(s) in {files} file(s).")
    return metrics


def apply_text_replacements(repo: Path, manifest: dict) -> None:
    for rel_text, replacements in manifest.get("textReplacements", {}).items():
        rel = safe_relative_path(rel_text)
        if not isinstance(replacements, list) or not replacements:
            raise UpdateError(f"textReplacements[{rel_text!r}] must be a non-empty array")
        target = repo_target(repo, rel)
        if not target.is_file():
            raise UpdateError(f"Text replacement target is missing: {rel}")
        text = target.read_text(encoding="utf-8")
        for index, item in enumerate(replacements, 1):
            if not isinstance(item, dict):
                raise UpdateError(f"Invalid text replacement #{index} for {rel}")
            old, new, expected = item.get("old"), item.get("new"), item.get("count", 1)
            if not isinstance(old, str) or not old or not isinstance(new, str) or not isinstance(expected, int) or expected < 1:
                raise UpdateError(f"Invalid text replacement #{index} for {rel}")
            actual = text.count(old)
            if actual != expected:
                raise UpdateError(
                    f"Text replacement base mismatch for {rel}: expected {expected}, found {actual}"
                )
            text = text.replace(old, new, expected)
        target.write_text(text, encoding="utf-8")


def apply_moves(repo: Path, manifest: dict) -> dict[str, str]:
    moves = manifest.get("operations", {}).get("moves", {})
    result: dict[str, str] = {}
    for raw_source, raw_target in moves.items():
        source_rel = safe_relative_path(raw_source)
        target_rel = safe_relative_path(raw_target)
        source = repo_target(repo, source_rel)
        target = repo_target(repo, target_rel)
        if not source.is_file():
            raise UpdateError(f"Move source is missing: {source_rel}")
        if target.exists():
            raise UpdateError(f"Move target already exists: {target_rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        result[source_rel.as_posix()] = target_rel.as_posix()
    return result


def apply_deletions(repo: Path, deletions: list[PurePosixPath]) -> None:
    for rel in deletions:
        target = repo_target(repo, rel)
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def build_state(manifest: dict) -> dict:
    return {
        "schemaVersion": 2,
        "appliedSequence": manifest["sequence"],
        "currentPackage": manifest["packageLabel"],
        "status": "complete",
    }


def prepare_generated_metadata(repo: Path, profile: str) -> None:
    if profile == "none":
        return
    for script in ("scripts/generate_release_metadata.py", "scripts/generate_checksums.py"):
        if (repo / script).is_file():
            subprocess.run([sys.executable, script], cwd=repo, check=True)


def run_validation(repo: Path, profile: str) -> None:
    for command in VALIDATION_PROFILES[profile]:
        print(f"::group::Validation: {' '.join(command)}")
        try:
            subprocess.run(command, cwd=repo, check=True)
        finally:
            print("::endgroup::")


def file_map(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root)
            if not should_ignore(rel):
                result[rel.as_posix()] = sha256_file(path)
    return result


def apply_candidate_diff(repo: Path, candidate: Path) -> tuple[list[str], list[str], list[str]]:
    before, after = file_map(repo), file_map(candidate)
    changed = sorted(path for path, digest in after.items() if before.get(path) != digest)
    deleted = sorted(path for path in before if path not in after)
    if any(path.startswith(WORKFLOW_PREFIX) for path in changed + deleted):
        raise UpdateError("Candidate validation attempted to modify GitHub workflow files")
    added = [path for path in changed if path not in before]
    replaced = [path for path in changed if path in before]
    touched = sorted(set(changed + deleted))
    with tempfile.TemporaryDirectory(prefix="inkdos-update-backup-") as backup_name:
        backup = Path(backup_name)
        snapshots: dict[str, Path | None] = {}
        try:
            for rel_text in touched:
                target = repo / rel_text
                if target.exists():
                    copy = backup / rel_text
                    copy.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, copy)
                    snapshots[rel_text] = copy
                else:
                    snapshots[rel_text] = None
            for rel_text in deleted:
                target = repo / rel_text
                if target.exists():
                    target.unlink()
            for rel_text in changed:
                source = candidate / rel_text
                target = repo / rel_text
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        except Exception:
            for rel_text in reversed(touched):
                target = repo / rel_text
                saved = snapshots.get(rel_text)
                if target.exists():
                    target.unlink()
                if saved is not None:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(saved, target)
            raise
    return added, replaced, deleted


def apply_package(
    package: Path,
    repo: Path,
    *,
    dry_run: bool = False,
    validation_override: str | None = None,
) -> dict:
    package, repo = package.resolve(), repo.resolve()
    if not package.is_file():
        raise UpdateError(f"Update package not found: {package}")
    if not (repo / VERSION_FILE).is_file():
        raise UpdateError(f"Not an InkDOS repository: {repo}")
    with tempfile.TemporaryDirectory(prefix="inkdos-update-stage-") as stage_name:
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
        verify_payload_contract(repo, payload, deletions, manifest)
        with tempfile.TemporaryDirectory(prefix="inkdos-update-candidate-") as candidate_name:
            candidate = Path(candidate_name) / "repository"
            copy_candidate(repo, candidate)
            overlay_payload(candidate, payload)
            merge_metrics = apply_file_merges(candidate, manifest)
            replacement_metrics = apply_tree_replacements(candidate, manifest)
            apply_text_replacements(candidate, manifest)
            move_metrics = apply_moves(candidate, manifest)
            apply_deletions(candidate, deletions)
            (candidate / STATE_FILE).write_text(
                json.dumps(build_state(manifest), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            prepare_generated_metadata(candidate, manifest["validationProfile"])
            run_validation(candidate, manifest["validationProfile"])
            before, after = file_map(repo), file_map(candidate)
            changed = sorted(path for path, digest in after.items() if before.get(path) != digest)
            added = [path for path in changed if path not in before]
            replaced = [path for path in changed if path in before]
            removed = sorted(path for path in before if path not in after)
            if not dry_run:
                added, replaced, removed = apply_candidate_diff(repo, candidate)
        return {
            "status": "validated" if dry_run else "applied",
            "rollback": False,
            "dryRun": dry_run,
            "packageLabel": manifest["packageLabel"],
            "targetRelease": manifest.get("targetRelease", "1.0"),
            "sequence": manifest["sequence"],
            "validationProfile": manifest["validationProfile"],
            "packageSha256": sha256_file(package),
            "added": added,
            "replaced": replaced,
            "deleted": removed,
            "copied": sorted(added + replaced),
            "validatedCandidate": True,
            "treeReplacements": replacement_metrics,
            "fileMerges": merge_metrics,
            "moves": move_metrics,
        }


def package_manifest_summary(package: Path) -> dict:
    try:
        with zipfile.ZipFile(package) as archive:
            value = json.loads(archive.read("patch-manifest.json").decode("utf-8"))
            return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_failure_report(path: Path, package: Path, repo: Path, error: Exception, *, dry_run: bool) -> None:
    manifest = package_manifest_summary(package)
    state = {}
    try:
        state = load_json(repo / STATE_FILE) if (repo / STATE_FILE).exists() else {}
    except Exception:
        pass
    report = {
        "status": "failed",
        "rollback": not dry_run,
        "error": str(error),
        "packageLabel": manifest.get("packageLabel", package.name),
        "targetRelease": manifest.get("targetRelease", "1.0"),
        "sequence": manifest.get("sequence"),
        "validationProfile": manifest.get("validationProfile", ""),
        "dryRun": dry_run,
        "repositorySequenceAfterRollback": state.get("appliedSequence", 0),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validation-profile", choices=sorted(VALIDATION_PROFILES))
    parser.add_argument("--report", type=Path)
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
                write_failure_report(args.report, args.package.resolve(), args.repo.resolve(), exc, dry_run=args.dry_run)
            except Exception as report_error:
                print(f"WARNING: could not write failure report: {report_error}", file=sys.stderr)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    verb = "validated" if args.dry_run else "applied"
    print(f"OK: {verb} InkDOS update package {plan['packageLabel']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
