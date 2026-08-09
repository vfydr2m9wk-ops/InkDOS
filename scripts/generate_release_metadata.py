#!/usr/bin/env python3
"""Synchronize deterministic InkDesk release metadata from VERSION.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def dump(name: str, value: dict) -> None:
    (ROOT / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    version = load("VERSION.json")
    release = version["version"]
    date = version.get("date", "")
    modules = list(version.get("components", {}).keys())

    build = load("BUILD_INFO.json")
    build.update({
        "product": "InkDesk",
        "version": release,
        "buildDate": date,
        "channel": version.get("releaseChannel", "beta"),
        "modules": modules,
        "requiresPreviousPackages": False,
    })
    dump("BUILD_INFO.json", build)

    source = load("SOURCE_MANIFEST.json")
    source.update({
        "product": "InkDesk",
        "version": release,
        "generatedAt": date,
        "entryPoint": "index.html",
    })
    dump("SOURCE_MANIFEST.json", source)

    release_manifest = load("RELEASE_MANIFEST.json")
    release_manifest.update({
        "project": "InkDesk",
        "version": release,
        "releaseName": version.get("releaseName", ""),
        "releaseDate": date,
    })
    dump("RELEASE_MANIFEST.json", release_manifest)

    print(f"Release metadata synchronized for InkDesk {release}.")


if __name__ == "__main__":
    main()
