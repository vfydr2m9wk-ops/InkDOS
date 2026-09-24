#!/usr/bin/env python3
from __future__ import annotations

from fnmatch import fnmatch
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS_PATH = ROOT / "config" / "components.json"
FROZEN_PATH = ROOT / "config" / "frozen-legacy.json"
VERSION_PATH = ROOT / "VERSION.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def component_map():
    payload = load_json(COMPONENTS_PATH)
    components = payload.get("components", {})
    if not isinstance(components, dict) or not components:
        raise SystemExit("config/components.json has no components")
    return components


def component(name: str):
    components = component_map()
    if name not in components:
        raise SystemExit(
            f"Unknown component {name!r}. Choose one of: {', '.join(sorted(components))}"
        )
    return components[name]


def product_version():
    return load_json(VERSION_PATH)["version"]


def frozen_registry():
    return load_json(FROZEN_PATH)


def normalize(path: Path | str):
    value = Path(path).as_posix()
    return value[2:] if value.startswith("./") else value


def matching_tests(name: str, include_browser: bool = False, full: bool = False):
    cfg = component(name)
    if not full:
        tests = list(cfg.get("smokeTests", []))
        if include_browser:
            tests.extend(cfg.get("browserSmokeTests", []))
        return sorted(dict.fromkeys(normalize(path) for path in tests))

    matches = set()
    for pattern in cfg.get("testGlobs", []):
        for path in ROOT.glob(pattern):
            if not path.is_file():
                continue
            if not include_browser and "_browser" in path.name:
                continue
            matches.add(normalize(path.relative_to(ROOT)))
    return sorted(matches)


def is_owned_path(name: str, rel_path: str):
    cfg = component(name)
    rel_path = normalize(rel_path)
    if rel_path in {normalize(p) for p in cfg.get("ownedPaths", [])}:
        return True
    for prefix in cfg.get("ownedPrefixes", []):
        if rel_path.startswith(normalize(prefix).rstrip("/") + "/"):
            return True
    for pattern in cfg.get("testGlobs", []):
        if fnmatch(rel_path, pattern):
            return True
    for path in cfg.get("smokeTests", []) + cfg.get("browserSmokeTests", []):
        if rel_path == normalize(path):
            return True
    return False


def git_output(*args: str):
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode:
        raise SystemExit(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def resolve_base(base: str):
    candidates = [base]
    if base == "main":
        candidates.insert(0, "origin/main")
    for candidate in candidates:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if proc.returncode == 0:
            return candidate
    raise SystemExit(f"Cannot resolve git base {base!r}")


def changed_paths(base: str):
    resolved = resolve_base(base)
    merge_base = git_output("merge-base", "HEAD", resolved)
    paths = set()

    committed = git_output("diff", "--name-only", f"{merge_base}...HEAD")
    paths.update(line for line in committed.splitlines() if line)

    unstaged = git_output("diff", "--name-only")
    paths.update(line for line in unstaged.splitlines() if line)

    staged = git_output("diff", "--cached", "--name-only")
    paths.update(line for line in staged.splitlines() if line)

    return sorted(normalize(path) for path in paths)


def command_for_test(rel_path: str):
    path = ROOT / rel_path
    suffix = path.suffix.lower()
    if suffix == ".py":
        return [sys.executable, rel_path]
    if suffix in {".js", ".cjs", ".mjs"}:
        return ["node", rel_path]
    raise SystemExit(f"No test runner configured for {rel_path}")
