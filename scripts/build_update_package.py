#!/usr/bin/env python3
"""Build deterministic InkDOS incremental update ZIPs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

FIXED_TIME = (1980, 1, 1, 0, 0, 0)
WORKFLOW_PREFIX = ".github/workflows/"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_path(raw: str) -> str:
    if not raw or "\\" in raw:
        raise SystemExit(f"Unsafe path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SystemExit(f"Unsafe path: {raw!r}")
    value = path.as_posix()
    if value == ".git" or value.startswith(".git/"):
        raise SystemExit(f"Git path is forbidden: {value}")
    if value == ".github/workflows" or value.startswith(WORKFLOW_PREFIX):
        raise SystemExit(f"Workflow path is forbidden in update ZIPs: {value}")
    return value


def write_member(zf: zipfile.ZipFile, name: str, data: bytes, mode: int = 0o644) -> None:
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--delete", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--file", action="append", default=[], help="Repository-relative payload path; repeat as needed")
    args = parser.parse_args()

    repo = args.repo.resolve()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("product") != "InkDOS":
        raise SystemExit("Manifest product must be InkDOS")
    if manifest.get("allowWorkflowChanges"):
        raise SystemExit("allowWorkflowChanges is forbidden")

    file_contract = manifest.setdefault("files", {})
    requested = list(args.file) or list(file_contract)
    if "scripts/apply_update_package.py" not in requested:
        requested.append("scripts/apply_update_package.py")

    payload: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for raw in requested:
        rel = safe_path(raw)
        folded = rel.casefold()
        if folded in seen:
            raise SystemExit(f"Duplicate/case-colliding payload path: {rel}")
        seen.add(folded)
        path = repo / rel
        if not path.is_file():
            raise SystemExit(f"Payload file does not exist: {rel}")
        digest = sha256(path)
        meta = file_contract.setdefault(rel, {})
        if not isinstance(meta, dict):
            raise SystemExit(f"Manifest files[{rel!r}] must be an object")
        if meta.get("sha256") and meta["sha256"] != digest:
            raise SystemExit(f"Manifest SHA-256 does not match payload: {rel}")
        meta["sha256"] = digest
        payload.append((rel, path))

    delete_lines: list[str] = []
    if args.delete and args.delete.exists():
        for line in args.delete.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            delete_lines.append(safe_path(value))
    deletion_contract = manifest.setdefault("deletions", {})
    if deletion_contract and set(deletion_contract) != set(delete_lines):
        raise SystemExit("Manifest deletions map must exactly match DELETE.txt")
    for rel in delete_lines:
        deletion_contract.setdefault(rel, {})

    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    delete_bytes = (("\n".join(delete_lines) + "\n") if delete_lines else "").encode("utf-8")

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w") as zf:
        write_member(zf, "patch-manifest.json", manifest_bytes)
        if delete_lines:
            write_member(zf, "DELETE.txt", delete_bytes)
        for rel, path in sorted(payload):
            mode = 0o755 if (path.stat().st_mode & 0o111) else 0o644
            write_member(zf, f"files/{rel}", path.read_bytes(), mode=mode)

    print(f"{output}  {sha256(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
