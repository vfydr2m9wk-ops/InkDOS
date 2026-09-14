#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import quote

PLATFORMS = {
    "windows-x86_64": (".exe", ".exe.sig"),
    "darwin-x86_64": (".app.tar.gz", ".app.tar.gz.sig"),
    "linux-x86_64": (".AppImage", ".AppImage.sig"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a static Tauri v2 updater manifest from signed release artifacts.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--assets", default="release-final")
    parser.add_argument("--notes", default="release-notes.md")
    parser.add_argument("--output", default="release-final/latest.json")
    parser.add_argument("--repository", default="vfydr2m9wk-ops/InkDOS")
    return parser.parse_args()


def exactly_one(root: Path, suffix: str) -> Path:
    matches = sorted(p for p in root.iterdir() if p.is_file() and p.name.endswith(suffix))
    if len(matches) != 1:
        rendered = ", ".join(p.name for p in matches) or "none"
        raise SystemExit(f"Expected exactly one *{suffix} updater asset, found {len(matches)}: {rendered}")
    return matches[0]


def main() -> int:
    args = parse_args()
    assets = Path(args.assets)
    if not assets.is_dir():
        raise SystemExit(f"Updater asset directory does not exist: {assets}")

    platforms: dict[str, dict[str, str]] = {}
    for platform, (artifact_suffix, signature_suffix) in PLATFORMS.items():
        artifact = exactly_one(assets, artifact_suffix)
        signature = exactly_one(assets, signature_suffix).read_text(encoding="utf-8").strip()
        if not signature:
            raise SystemExit(f"Updater signature is empty for {artifact.name}")
        platforms[platform] = {
            "url": f"https://github.com/{args.repository}/releases/download/{quote(args.tag, safe='')}/{quote(artifact.name)}",
            "signature": signature,
        }

    notes_path = Path(args.notes)
    manifest = {
        "version": args.version,
        "notes": notes_path.read_text(encoding="utf-8") if notes_path.exists() else "",
        "platforms": platforms,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
