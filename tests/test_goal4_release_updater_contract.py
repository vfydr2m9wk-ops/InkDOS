#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
MANIFEST = ROOT / "desktop" / "scripts" / "build_updater_manifest.py"
CONFIG = ROOT / "desktop" / "scripts" / "prepare_updater_release_config.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    require(CONFIG.exists(), "release updater must generate an ephemeral Tauri release config")
    require(MANIFEST.exists(), "release updater must generate latest.json deterministically")

    require("TAURI_SIGNING_PRIVATE_KEY" in workflow, "release build must receive the Tauri signing private key from Actions secrets")
    require("TAURI_SIGNING_PRIVATE_KEY_PASSWORD" in workflow, "release build must receive the Tauri signing key password from Actions secrets")
    require("TAURI_UPDATER_PUBLIC_KEY" in workflow, "release build must receive the public updater key from an Actions variable/secret")
    require("prepare_updater_release_config.py" in workflow, "release build must prepare a signed-updater-only config")
    require("createUpdaterArtifacts" not in (ROOT / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"), "normal development/package builds must not require release signing secrets")
    require("--config" in workflow and "tauri.updater.release.conf.json" in workflow, "release build must merge the ephemeral updater config")

    signature_patterns = ("*.exe.sig", "*.app.tar.gz.sig", "*.AppImage.sig")
    require(all(pattern in workflow for pattern in signature_patterns), "release artifacts must include Windows, macOS, and Linux updater signatures")
    require("*.app.tar.gz" in workflow, "macOS updater archive must be published")
    require("build_updater_manifest.py" in workflow, "publish job must generate latest.json")
    require("latest.json" in workflow, "latest.json must be published with the release")

    require("asset_count" not in workflow or "-ne 6" not in workflow, "release validation must not assume exactly six total assets after updater artifacts are added")
    require("/releases/download/" in MANIFEST.read_text(encoding="utf-8"), "latest.json URLs must target immutable assets in the same tagged GitHub Release")
    require("signature" in MANIFEST.read_text(encoding="utf-8"), "latest.json must bind each platform artifact to its signature")

    print("Goal 4 signed release updater contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
