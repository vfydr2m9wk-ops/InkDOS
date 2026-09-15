#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an ephemeral Tauri config for signed InkDOS updater artifacts.")
    parser.add_argument("--pubkey", required=True, help="Tauri updater public key contents (never a file path).")
    parser.add_argument("--output", default="desktop/src-tauri/tauri.updater.release.conf.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pubkey = args.pubkey.strip()
    if not pubkey or pubkey == "INKDOS_UPDATER_PUBLIC_KEY_REQUIRED":
        raise SystemExit("A real Tauri updater public key is required for release builds.")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "bundle": {"createUpdaterArtifacts": True},
        "plugins": {"updater": {"pubkey": pubkey}},
    }
    output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(output.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
