#!/usr/bin/env python3
"""Synchronize current InkDOS release metadata from VERSION.json.

This generator writes only present-state metadata. Historical milestones belong to
Git history and release records, not to the active application manifests.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/vfydr2m9wk-ops/InkDOS"
DEMO = "https://vfydr2m9wk-ops.github.io/InkDOS/"
HISTORICAL_KEYS = {
    "originMilestone",
    "modelRelease",
    "dragControllerRelease",
    "architectureRelease",
    "sourceDevelopmentLine",
    "releaseNotesOrganization",
}


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def dump(name: str, value: dict) -> None:
    (ROOT / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def prune_history(value):
    if isinstance(value, dict):
        return {
            key: prune_history(item)
            for key, item in value.items()
            if key not in HISTORICAL_KEYS
        }
    if isinstance(value, list):
        return [prune_history(item) for item in value]
    return value


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

    build = prune_history(load("BUILD_INFO.json"))
    build.update({
        "product": "InkDOS",
        "version": release,
        "buildDate": date,
        "channel": version.get("releaseChannel", "beta"),
        "modules": modules,
        "requiresPreviousPackages": False,
    })
    dump("BUILD_INFO.json", build)

    source = prune_history(load("SOURCE_MANIFEST.json"))
    source.update({
        "product": "InkDOS",
        "version": release,
        "generatedAt": date,
        "entryPoint": "index.html",
        "updateWorkflow": ".github/workflows/apply-inkdos-update.yml",
        "workflowPolicy": "validated candidate; update ZIPs cannot modify GitHub workflows",
    })
    dump("SOURCE_MANIFEST.json", source)

    release_manifest = prune_history(load("RELEASE_MANIFEST.json"))
    release_manifest.update({
        "project": "InkDOS",
        "version": release,
        "releaseName": version.get("releaseName", ""),
        "releaseDate": date,
        "repository": REPOSITORY,
        "homepage": DEMO,
        "license": "MIT for InkDOS original code; bundled third-party components retain upstream licenses.",
    })
    if isinstance(release_manifest.get("entryPoints"), dict):
        release_manifest["entryPoints"].pop("InkDOS.html", None)
    dump("RELEASE_MANIFEST.json", release_manifest)

    app_manifest = prune_history(load("app-manifest.json"))
    app_manifest.update({
        "id": "inkdos",
        "name": "InkDOS",
        "longName": "Ink Desk Offline Suite",
        "tagline": "Local. Offline. Private.",
        "version": release,
        "source": REPOSITORY,
        "homepage": DEMO,
    })
    app_manifest["release"] = {
        "version": release,
        "channel": version.get("releaseChannel", "beta"),
        "name": version.get("releaseName", ""),
        "date": date,
        "consolidated": True,
    }
    if isinstance(app_manifest.get("update"), dict):
        app_manifest["update"].update({
            "repository": "vfydr2m9wk-ops/InkDOS",
            "assetPattern": "InkDOS_v*.zip",
        })
        app_manifest["update"].pop("nextPatch", None)
    if isinstance(app_manifest.get("homeRefinement"), dict):
        app_manifest["homeRefinement"].pop("universalOpenCopy", None)
        app_manifest["homeRefinement"].pop("moduleCardsBeforeUniversalOpen", None)
    ui = app_manifest.get("uiSystem")
    if isinstance(ui, dict):
        visual = ui.pop("visualRefresh0203", None)
        if isinstance(visual, dict):
            visual = prune_history(visual)
            visual.pop("stylesheet", None)
            visual["stylesheets"] = [
                "shared/ui/visual.css",
                "shared/ui/content.css",
                "shared/ui/workspace.css",
                "shared/ui/polish.css",
            ]
            visual["documentation"] = "docs/VISUAL_SYSTEM.md"
            visual["version"] = release
            ui["currentVisualLayer"] = visual
    if isinstance(app_manifest.get("pdfReviewSystem"), dict):
        app_manifest["pdfReviewSystem"]["storageSchema"] = "inkdos-pdf-review/2"
    dump("app-manifest.json", app_manifest)

    sbom = prune_history(load("SBOM.spdx.json"))
    sbom["name"] = f"InkDOS-v{release}"
    sbom["documentNamespace"] = f"{REPOSITORY}/releases/tag/v{release}"
    sbom.setdefault("creationInfo", {})["created"] = f"{date}T00:00:00Z" if date else ""
    for package in sbom.get("packages", []):
        if package.get("name") == "InkDOS":
            package["versionInfo"] = release
    dump("SBOM.spdx.json", sbom)

    print(f"Release metadata synchronized for InkDOS {release}.")


if __name__ == "__main__":
    main()
