#!/usr/bin/env python3
"""Update only declared CHECKSUMS.sha256 entries for an incremental patch.

This helper deliberately preserves every checksum that is not named on the
command line. That makes an incomplete local checkout safe for patch authoring:
files that exist only in the authoritative hosted tree keep their approved
hashes instead of being silently removed or replaced by local reconstructions.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import sys

LINE_PATTERN = re.compile(r"^([0-9a-fA-F]{64})  (.+)$")
EXCLUDED_PARTS = {".git", ".mobile-import", "__pycache__", "_site", "test-results"}
EXCLUDED_NAMES = {"CHECKSUMS.sha256", "DEVELOPMENT_STATE.json", ".DS_Store", "Thumbs.db"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}


class ChecksumUpdateError(RuntimeError):
    pass


def normalize_relative(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip() or "\\" in raw:
        raise ChecksumUpdateError(f"Invalid repository-relative path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ChecksumUpdateError(f"Unsafe repository-relative path: {raw!r}")
    return path.as_posix()


def is_distributable(relative: str) -> bool:
    path = PurePosixPath(relative)
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.parts[:3] == ("tests", "browser", "results"):
        return False
    if path.name in EXCLUDED_NAMES or Path(path.name).suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return True


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def load_manifest(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ChecksumUpdateError(f"Checksum manifest not found: {path}")
    entries: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        match = LINE_PATTERN.fullmatch(raw)
        if not match:
            raise ChecksumUpdateError(f"Invalid checksum line {number}: {raw}")
        checksum, relative = match.groups()
        relative = normalize_relative(relative)
        if relative in entries:
            raise ChecksumUpdateError(f"Duplicate checksum entry: {relative}")
        entries[relative] = checksum.lower()
    return entries


def update_manifest(
    root: Path,
    manifest: Path,
    *,
    changed: list[str],
    deleted: list[str],
) -> dict[str, str]:
    root = root.resolve()
    entries = load_manifest(manifest)
    changed_paths = [normalize_relative(value) for value in changed]
    deleted_paths = [normalize_relative(value) for value in deleted]
    overlap = sorted(set(changed_paths) & set(deleted_paths))
    if overlap:
        raise ChecksumUpdateError(
            "Paths cannot be both changed and deleted: " + ", ".join(overlap)
        )

    for relative in deleted_paths:
        entries.pop(relative, None)

    for relative in changed_paths:
        if not is_distributable(relative):
            raise ChecksumUpdateError(
                f"Path is excluded from the distributable checksum tree: {relative}"
            )
        path = root.joinpath(*PurePosixPath(relative).parts)
        try:
            path.resolve().relative_to(root)
        except ValueError as exc:
            raise ChecksumUpdateError(f"Path escapes the repository: {relative}") from exc
        if not path.is_file():
            raise ChecksumUpdateError(
                f"Changed path does not exist as a file; use --delete for removals: {relative}"
            )
        entries[relative] = digest(path)

    manifest.write_text(
        "".join(f"{entries[name]}  {name}\n" for name in sorted(entries)),
        encoding="utf-8",
    )
    return entries


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Checksum manifest to edit; defaults to <repo>/CHECKSUMS.sha256",
    )
    parser.add_argument(
        "--changed",
        action="append",
        default=[],
        metavar="PATH",
        help="Repository-relative file whose checksum must be recomputed; repeat as needed",
    )
    parser.add_argument(
        "--delete",
        action="append",
        default=[],
        metavar="PATH",
        help="Repository-relative file whose existing manifest entry must be removed",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo.resolve()
    manifest = (args.manifest or (repo / "CHECKSUMS.sha256")).resolve()
    if not args.changed and not args.delete:
        print("No checksum paths were declared; nothing changed.")
        return 0
    try:
        before = load_manifest(manifest)
        after = update_manifest(
            repo,
            manifest,
            changed=args.changed,
            deleted=args.delete,
        )
    except (ChecksumUpdateError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    touched = len(set(args.changed) | set(args.delete))
    print(
        f"Updated {touched} declared checksum path(s); "
        f"preserved {len(set(before) - set(args.changed) - set(args.delete))} untouched entry/entries; "
        f"manifest now contains {len(after)} entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
