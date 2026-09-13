#!/usr/bin/env python3
"""Materialize native workspace icons from the canonical InkDOS icon sources.

This runs only as an explicit desktop bundle hook. It does not touch the canonical
assets; it derives Windows ICOs (and the other standard Tauri icon outputs) into
an ignored packaging directory used by the installed workspace launchers.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TAURI_DIR = ROOT / "desktop" / "src-tauri"
LAUNCHERS_PATH = ROOT / "desktop" / "launchers.json"
OUTPUT_ROOT = TAURI_DIR / "windows" / "workspace-icons"


def main() -> None:
    launchers = json.loads(LAUNCHERS_PATH.read_text(encoding="utf-8"))
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)

    for workspace, launcher in launchers.items():
        source = ROOT / launcher["icon"]
        if not source.is_file():
            raise SystemExit(f"Missing canonical workspace icon source: {source}")

        output = OUTPUT_ROOT / workspace
        output.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["cargo", "tauri", "icon", str(source), "--output", str(output)],
            cwd=TAURI_DIR,
            check=True,
        )

        native_icon = output / "icon.ico"
        if not native_icon.is_file():
            raise SystemExit(
                f"Tauri icon generation did not produce Windows ICO for {workspace}: {native_icon}"
            )

    print(f"Generated {len(launchers)} workspace native icon sets from canonical sources.")


if __name__ == "__main__":
    main()
