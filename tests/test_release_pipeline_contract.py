#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


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

    require("bundles: app,dmg" in text, "macOS release build does not request the updater app bundle")
    require("*.app.tar.gz" in text and "*.app.tar.gz.sig" in text, "macOS updater artifacts are not required")

    require("reuse_run_id:" in text, "release workflow has no artifact-reuse input")
    require("run-id: ${{ inputs.reuse_run_id }}" in text, "prior-run artifacts are not reusable")
    require("github-token: ${{ github.token }}" in text, "cross-run artifact download lacks an Actions token")
    require("Release-Provenance" in text, "release artifacts lack immutable provenance")
    require("Verify artifact provenance" in text, "publish-only retry does not verify artifact provenance")
    require("actions: read" in text, "publish job cannot read artifacts from a prior run")

    print("InkDOS resilient release pipeline contract: PASS")


if __name__ == "__main__":
    main()
