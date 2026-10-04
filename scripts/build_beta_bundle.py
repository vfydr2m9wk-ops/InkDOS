#!/usr/bin/env python3
"""Build the desktop beta-tools bundle (signed separately, delivered without a desktop release).

    stage --out DIR --version N --commit SHA   write DIR/manifest.json and DIR/files/<path>
    pack DIR OUT.tar.gz                        pack a staged, signed DIR (manifest.json.sig required)

The desktop host verifies manifest.json.sig against its pinned beta-channel public key, then
checks every file against the SHA-256 listed in the manifest. config/beta-channel.json lists
the tools and the repository paths the bundle carries.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "beta-channel.json"
MAX_BUNDLE_BYTES = 64 * 1024 * 1024
SAFE_PATH = re.compile(r"^[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def load_config() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("schema") != 1 or config.get("channel") != "beta-tools":
        raise SystemExit("config/beta-channel.json: unsupported schema or channel")
    if not VERSION.match(str(config.get("minDesktop", ""))):
        raise SystemExit("config/beta-channel.json: minDesktop must be X.Y.Z")
    return config


def safe_relative(path: str) -> str:
    pure = PurePosixPath(path)
    if not SAFE_PATH.match(path) or pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise SystemExit(f"unsafe bundle path: {path!r}")
    return path


def collect(config: dict) -> list[str]:
    files: set[str] = set()
    for entry in config["include"]:
        source = ROOT / entry
        if entry.endswith("/"):
            if not source.is_dir():
                raise SystemExit(f"missing directory: {entry}")
            for path in source.rglob("*"):
                if path.is_file() and path.name != ".DS_Store":
                    files.add(path.relative_to(ROOT).as_posix())
        elif source.is_file():
            files.add(entry)
        else:
            raise SystemExit(f"missing file: {entry}")
    for tool in config["tools"]:
        if tool["entry"] not in files:
            raise SystemExit(f"tool entry not in bundle: {tool['entry']}")
    return sorted(safe_relative(path) for path in files)


def stage(out: Path, version: int, commit: str) -> Path:
    if version < 1:
        raise SystemExit("version must be a positive integer")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("commit must be a full lowercase SHA-1")
    config = load_config()
    if out.exists():
        shutil.rmtree(out)
    (out / "files").mkdir(parents=True)
    hashes: dict[str, str] = {}
    total = 0
    for rel in collect(config):
        data = (ROOT / rel).read_bytes()
        total += len(data)
        hashes[rel] = hashlib.sha256(data).hexdigest()
        target = out / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if total > MAX_BUNDLE_BYTES:
        raise SystemExit(f"bundle too large: {total} bytes")
    manifest = {
        "schema": 1,
        "channel": "beta-tools",
        "version": version,
        "commit": commit,
        "minDesktop": config["minDesktop"],
        "tools": [{"id": t["id"], "title": t["title"], "entry": t["entry"]} for t in config["tools"]],
        "files": hashes,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out / "manifest.json"


def _add(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o644
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    tar.addfile(info, io.BytesIO(data))


def pack(staged: Path, out: Path) -> None:
    manifest_bytes = (staged / "manifest.json").read_bytes()
    signature = staged / "manifest.json.sig"
    if not signature.is_file():
        raise SystemExit("manifest.json.sig is missing: sign manifest.json before packing")
    manifest = json.loads(manifest_bytes)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        _add(tar, "manifest.json", manifest_bytes)
        _add(tar, "manifest.json.sig", signature.read_bytes())
        for rel in sorted(manifest["files"]):
            data = (staged / "files" / safe_relative(rel)).read_bytes()
            if hashlib.sha256(data).hexdigest() != manifest["files"][rel]:
                raise SystemExit(f"staged file changed after manifest: {rel}")
            _add(tar, "files/" + rel, data)
    out.write_bytes(gzip.compress(raw.getvalue(), compresslevel=9, mtime=0))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("stage")
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--version", type=int, required=True)
    s.add_argument("--commit", required=True)
    p = sub.add_parser("pack")
    p.add_argument("staged", type=Path)
    p.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "stage":
        print(stage(args.out, args.version, args.commit))
    else:
        pack(args.staged, args.out)
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
