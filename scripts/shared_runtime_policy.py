#!/usr/bin/env python3
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "shared-runtime-policy.json"


@lru_cache(maxsize=1)
def _load_policy() -> tuple[frozenset[str], tuple[str, ...]]:
    data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise RuntimeError("unsupported shared runtime policy version")

    files = frozenset(str(item) for item in data.get("allowedFiles", []))
    prefixes = tuple(str(item) for item in data.get("allowedPrefixes", []))

    for item in (*files, *prefixes):
        path = PurePosixPath(item)
        if not item or path.is_absolute() or ".." in path.parts or "\\" in item:
            raise RuntimeError(f"invalid shared runtime policy entry: {item!r}")
    for prefix in prefixes:
        if not prefix.endswith("/"):
            raise RuntimeError(f"shared runtime prefix must end with '/': {prefix!r}")

    return files, prefixes


def is_allowed_shared_relpath(relpath: str) -> bool:
    if not isinstance(relpath, str) or not relpath:
        return False
    path = PurePosixPath(relpath)
    if path.is_absolute() or ".." in path.parts or "\\" in relpath:
        return False
    normalized = path.as_posix()
    files, prefixes = _load_policy()
    return normalized in files or any(normalized.startswith(prefix) for prefix in prefixes)


if __name__ == "__main__":
    files, prefixes = _load_policy()
    print(f"Shared runtime policy loaded: {len(files)} exact files, {len(prefixes)} prefixes")
