#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
PROMOTION_WORKFLOW = ROOT / ".github" / "workflows" / "promote-release-tag.yml"
PROMOTION_REQUEST = ROOT / ".github" / "release-promotion.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    require("Signing preflight" in text, "release workflow has no signing preflight")
    require("cargo tauri signer sign" in text, "signing preflight does not exercise the Tauri signer")
    require("TAURI_SIGNING_PRIVATE_KEY" in text, "signing private key is not wired into preflight")
    require("TAURI_SIGNING_PRIVATE_KEY_PASSWORD" in text, "signing password is not wired into preflight")
    require("TAURI_UPDATER_PUBLIC_KEY" in text, "updater public key is not validated before build")

    require("v*.*.*" in text, "release workflow is not tag-triggered")
    require("workflow_dispatch" not in text, "release workflow still exposes a manual publication path")
    require("reuse_run_id" not in text, "release workflow still exposes cross-run artifact reuse")
    require("inputs." not in text, "release workflow still depends on manual inputs")
    require(not PROMOTION_WORKFLOW.exists(), "redundant release promotion workflow still exists")
    require(not PROMOTION_REQUEST.exists(), "redundant release promotion state still exists")

    require("bundles: nsis" in text, "Windows release build does not use NSIS")
    require("bundles: app,dmg" in text, "macOS release build does not request the updater app bundle")
    require("bundles: appimage" in text, "Linux release build does not use AppImage")
    require("*.app.tar.gz" in text and "*.app.tar.gz.sig" in text, "macOS updater artifacts are not required")
    require("bundles: nsis,msi" not in text, "MSI is still built")
    require("bundles: deb,appimage,rpm" not in text, "DEB/RPM are still built")

    require("Release-Provenance" in text, "release artifacts lack immutable provenance")
    require("Verify artifact provenance" in text, "publish job does not verify artifact provenance")
    require("Download current-run native artifacts" in text, "publish job does not use current-run artifacts")
    require("Download current-run provenance" in text, "publish job does not use current-run provenance")
    require("run-id:" not in text, "publish job can still select a prior workflow run")
    require("github-token:" not in text, "publish job still has cross-run download wiring")
    require("actions: read" in text, "publish job cannot read artifacts from its own run")

    print("InkDOS tag-only release pipeline contract: PASS")


if __name__ == "__main__":
    main()
