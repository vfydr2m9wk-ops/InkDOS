#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "desktop" / "scripts" / "prepare_updater_release_config.py"
MANIFEST = ROOT / "desktop" / "scripts" / "build_updater_manifest.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        release_config = temp / "tauri.release.json"

        rejected = run(
            str(CONFIG),
            "--pubkey",
            "INKDOS_UPDATER_PUBLIC_KEY_REQUIRED",
            "--output",
            str(release_config),
        )
        require(rejected.returncode != 0, "release config must fail closed on the development placeholder key")
        require(not release_config.exists(), "failed release config generation must not leave a trusted-looking config")

        public_key = "dGVzdC11cGRhdGVyLXB1YmxpYy1rZXk="
        accepted = run(str(CONFIG), "--pubkey", public_key, "--output", str(release_config))
        require(accepted.returncode == 0, f"valid release config generation failed: {accepted.stderr}")
        config = json.loads(release_config.read_text(encoding="utf-8"))
        require(config["bundle"]["createUpdaterArtifacts"] is True, "release config must enable updater artifacts")
        require(config["plugins"]["updater"]["pubkey"] == public_key, "release config must embed the supplied public key exactly")

        assets = temp / "assets"
        assets.mkdir()
        fixtures = {
            "InkDOS_2.3.0_x64-setup.exe": b"windows",
            "InkDOS_2.3.0_x64-setup.exe.sig": b"WINDOWS_SIGNATURE\n",
            "InkDOS.app.tar.gz": b"macos",
            "InkDOS.app.tar.gz.sig": b"MACOS_SIGNATURE\n",
            "InkDOS_2.3.0_amd64.AppImage": b"linux",
            "InkDOS_2.3.0_amd64.AppImage.sig": b"LINUX_SIGNATURE\n",
        }
        for name, data in fixtures.items():
            (assets / name).write_bytes(data)

        notes = temp / "notes.md"
        notes.write_text("InkDOS 2.3 release notes.\n", encoding="utf-8")
        output = temp / "latest.json"
        built = run(
            str(MANIFEST),
            "--version",
            "2.3.0",
            "--tag",
            "v2.3.0",
            "--assets",
            str(assets),
            "--notes",
            str(notes),
            "--output",
            str(output),
        )
        require(built.returncode == 0, f"updater manifest generation failed: {built.stderr}")
        manifest = json.loads(output.read_text(encoding="utf-8"))
        require(manifest["version"] == "2.3.0", "manifest version must match the release version")
        require(manifest["notes"] == "InkDOS 2.3 release notes.\n", "manifest must preserve release notes")
        require(set(manifest["platforms"]) == {"windows-x86_64", "darwin-x86_64", "linux-x86_64"}, "manifest must cover the supported desktop updater targets")

        expected_signatures = {
            "windows-x86_64": "WINDOWS_SIGNATURE",
            "darwin-x86_64": "MACOS_SIGNATURE",
            "linux-x86_64": "LINUX_SIGNATURE",
        }
        for platform, signature in expected_signatures.items():
            entry = manifest["platforms"][platform]
            require(entry["signature"] == signature, f"{platform} signature must be embedded literally")
            require("/releases/download/v2.3.0/" in entry["url"], f"{platform} URL must bind to the tagged release")
            require(entry["url"].startswith("https://github.com/vfydr2m9wk-ops/InkDOS/"), f"{platform} URL must stay on the canonical repository")

        (assets / "InkDOS_2.3.0_amd64.AppImage.sig").unlink()
        rejected_manifest = run(
            str(MANIFEST),
            "--version",
            "2.3.0",
            "--tag",
            "v2.3.0",
            "--assets",
            str(assets),
            "--notes",
            str(notes),
            "--output",
            str(temp / "invalid.json"),
        )
        require(rejected_manifest.returncode != 0, "manifest generation must fail closed when a platform signature is missing")

    print("Goal 4 release helper behavior contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
