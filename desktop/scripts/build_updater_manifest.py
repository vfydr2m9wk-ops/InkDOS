#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import quote

PLATFORMS = {
    "windows-x86_64": (".exe", ".exe.sig"),
    "darwin-aarch64": (".app.tar.gz", ".app.tar.gz.sig"),
    "linux-x86_64": (".AppImage", ".AppImage.sig"),
}

VERSIONED_ARTIFACT_PREFIX = {
    "windows-x86_64": "InkDOS_{version}_",
    "linux-x86_64": "InkDOS_{version}_",
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
    expected_tag = f"v{args.version}"
    if args.tag != expected_tag:
        raise SystemExit(f"Updater tag/version mismatch: tag={args.tag!r}, expected {expected_tag!r}")
    assets = Path(args.assets)
    if not assets.is_dir():
        raise SystemExit(f"Updater asset directory does not exist: {assets}")

    platforms: dict[str, dict[str, str]] = {}
    for platform, (artifact_suffix, signature_suffix) in PLATFORMS.items():
        artifact = exactly_one(assets, artifact_suffix)
        prefix_template = VERSIONED_ARTIFACT_PREFIX.get(platform)
        if prefix_template and not artifact.name.startswith(prefix_template.format(version=args.version)):
            raise SystemExit(
                f"Updater artifact/version mismatch for {platform}: artifact={artifact.name!r}, version={args.version!r}"
            )
        signature_path = exactly_one(assets, signature_suffix)
        if signature_path.name != artifact.name + ".sig":
            raise SystemExit(
                f"Updater artifact/signature mismatch for {platform}: artifact={artifact.name!r}, signature={signature_path.name!r}"
            )
        signature = signature_path.read_text(encoding="utf-8").strip()
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
