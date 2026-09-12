#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / "VERSION.json"
TAURI_CONFIG = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def product_version() -> str:
    data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    version = str(data.get("version", "")).strip()
    if not SEMVER.fullmatch(version):
        raise SystemExit(f"VERSION.json contains invalid semantic version: {version!r}")
    return version


def expected_tag(version: str) -> str:
    return f"v{version}"


def check_tag(tag: str) -> None:
    version = product_version()
    expected = expected_tag(version)
    if tag != expected:
        raise SystemExit(f"release tag/version mismatch: tag={tag!r}, expected={expected!r}")
    print(f"InkDOS release tag matches VERSION.json: {tag}")


def tauri_config() -> dict:
    return json.loads(TAURI_CONFIG.read_text(encoding="utf-8"))


def check_config() -> None:
    version = product_version()
    configured = str(tauri_config().get("version", "")).strip()
    if configured != version:
        raise SystemExit(
            f"Tauri version mismatch: tauri.conf.json={configured!r}, VERSION.json={version!r}. "
            "Run release_version.py --sync-config."
        )
    print(f"Tauri version matches VERSION.json: {version}")


def sync_config() -> None:
    version = product_version()
    config = tauri_config()
    previous = str(config.get("version", "")).strip()
    config["version"] = version
    TAURI_CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    if previous == version:
        print(f"Tauri version already synchronized: {version}")
    else:
        print(f"Tauri version synchronized: {previous or '<unset>'} -> {version}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate InkDOS release and Tauri version metadata.")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check-config", action="store_true", help="verify tauri.conf.json matches VERSION.json")
    actions.add_argument("--sync-config", action="store_true", help="write VERSION.json version into tauri.conf.json")
    actions.add_argument("--check-tag", metavar="TAG", help="verify TAG is exactly v<version> from VERSION.json")
    args = parser.parse_args()

    if args.check_config:
        check_config()
    elif args.sync_config:
        sync_config()
    else:
        check_tag(args.check_tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
