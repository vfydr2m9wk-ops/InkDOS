#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESKTOP = ROOT / "desktop"
DIST = DESKTOP / "web-dist"
BRIDGE = DESKTOP / "desktop-host.js"
HEAD_TAG = "<head>"
INJECTION = '<script src="/desktop-host.js"></script>'
ROOT_FILES = ("index.html", "manifest.webmanifest", "service-worker.js", "VERSION.json")
ROOT_DIRS = ("assets", "apps")
DOC_FILES = ("PROJECT_STATUS.md", "KNOWN_LIMITATIONS.md")


def _copy_runtime(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in ROOT_FILES:
        source = ROOT / name
        if source.exists():
            shutil.copy2(source, destination / name)
    for name in ROOT_DIRS:
        source = ROOT / name
        if source.exists():
            shutil.copytree(source, destination / name)
    docs = destination / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    for name in DOC_FILES:
        source = ROOT / "docs" / name
        if source.exists():
            shutil.copy2(source, docs / name)
    shutil.copy2(BRIDGE, destination / "desktop-host.js")


def _inject_bridge(destination: Path) -> int:
    count = 0
    for html in destination.rglob("*.html"):
        text = html.read_text(encoding="utf-8")
        if INJECTION in text:
            if text.count(INJECTION) != 1:
                raise RuntimeError(f"desktop bridge duplicated in {html.relative_to(destination)}")
        else:
            replaced, substitutions = re.subn(
                r"<head(?:\s[^>]*)?>",
                lambda match: match.group(0) + INJECTION,
                text,
                count=1,
                flags=re.IGNORECASE,
            )
            if substitutions != 1:
                raise RuntimeError(f"no <head> found in {html.relative_to(destination)}")
            html.write_text(replaced, encoding="utf-8")
        count += 1
    if count == 0:
        raise RuntimeError("no HTML entry points were staged")
    return count


def _validate(destination: Path) -> None:
    required = [destination / "index.html", destination / "desktop-host.js", destination / "apps", destination / "assets"]
    missing = [path.relative_to(destination) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"staged runtime is incomplete: {missing}")
    for html in destination.rglob("*.html"):
        text = html.read_text(encoding="utf-8")
        if text.count(INJECTION) != 1:
            raise RuntimeError(f"desktop bridge injection invalid in {html.relative_to(destination)}")


def stage(destination: Path) -> int:
    if destination.exists():
        shutil.rmtree(destination)
    _copy_runtime(destination)
    count = _inject_bridge(destination)
    _validate(destination)
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage InkDOS web assets for the Tauri desktop host.")
    parser.add_argument("--check", action="store_true", help="stage in a temporary directory and validate without changing web-dist")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="inkdos-tauri-") as temp:
            count = stage(Path(temp) / "web-dist")
            print(f"InkDOS desktop staging check passed: {count} HTML entry points")
        return 0

    count = stage(DIST)
    print(f"InkDOS desktop runtime staged at {DIST}: {count} HTML entry points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
