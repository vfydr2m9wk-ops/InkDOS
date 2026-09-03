#!/usr/bin/env python3
"""Synchronize deterministic InkDesk release metadata from VERSION.json."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def dump(name: str, value: dict) -> None:
    (ROOT / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def sync_product_config(release: str) -> None:
    path = ROOT / "shared/product-config.js"
    source = path.read_text(encoding="utf-8")
    source = re.sub(r"name:'[^']+'", "name:'InkDOS'", source, count=1)
    source = re.sub(r"longName:'[^']+'", "longName:'Ink Desk Offline Suite'", source, count=1)
    source = re.sub(r"tagline:'[^']+'", "tagline:'Local. Offline. Private.'", source, count=1)
    source = re.sub(r"version:'[^']+'", f"version:'{release}'", source, count=1)
    path.write_text(source, encoding="utf-8")


def main() -> None:
    version = load("VERSION.json")
    release = version["version"]
    date = version.get("date", "")
    modules = list(version.get("components", {}).keys())
    sync_product_config(release)

    build = load("BUILD_INFO.json")
    build.update({
        "product": "InkDOS",
        "version": release,
        "buildDate": date,
        "channel": version.get("releaseChannel", "beta"),
        "modules": modules,
        "requiresPreviousPackages": False,
    })
    dump("BUILD_INFO.json", build)

    source = load("SOURCE_MANIFEST.json")
    source.update({
        "product": "InkDOS",
        "version": release,
        "generatedAt": date,
        "entryPoint": "index.html",
    })
    dump("SOURCE_MANIFEST.json", source)

    release_manifest = load("RELEASE_MANIFEST.json")
    release_manifest.update({
        "project": "InkDOS",
        "version": release,
        "releaseName": version.get("releaseName", ""),
        "releaseDate": date,
    })
    dump("RELEASE_MANIFEST.json", release_manifest)

    app_manifest = load("app-manifest.json")
    app_manifest["version"] = release
    app_manifest["release"] = {
        "version": release,
        "channel": version.get("releaseChannel", "beta"),
        "name": version.get("releaseName", ""),
        "date": date,
        "consolidated": True,
        "sourceDevelopmentLine": "0.20.x stabilization",
        "publicVersioning": (
            "Semantic prereleases on the 1.0 line; internal update sequence is independent."
        ),
    }
    if isinstance(app_manifest.get("homeRefinement"), dict):
        app_manifest["homeRefinement"].pop("universalOpenCopy", None)
        app_manifest["homeRefinement"].pop("moduleCardsBeforeUniversalOpen", None)
    if isinstance(app_manifest.get("update"), dict):
        app_manifest["update"].pop("nextPatch", None)
    dump("app-manifest.json", app_manifest)

    sbom = load("SBOM.spdx.json")
    sbom["name"] = f"InkDOS-v{release}"
    sbom["documentNamespace"] = (
        f"https://github.com/vfydr2m9wk-ops/InkDesk/releases/tag/v{release}"
    )
    sbom.setdefault("creationInfo", {})["created"] = f"{date}T00:00:00Z" if date else ""
    for package in sbom.get("packages", []):
        if package.get("SPDXID") == "SPDXRef-Package-InkDesk" or package.get("name") == "InkDesk":
            package["name"] = "InkDOS"
            package["versionInfo"] = release
    dump("SBOM.spdx.json", sbom)

    print(f"Release metadata synchronized for InkDOS {release}.")


if __name__ == "__main__":
    main()
