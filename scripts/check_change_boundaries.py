#!/usr/bin/env python3
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRODUCT_PREFIXES = ("apps/", "shared/")
PRODUCT_EXACT = {"desktop/desktop-host.js"}
RELEASE_CONTROL_EXACT = {
    ".github/workflows/release.yml",
    "config/release-authorization.json",
    "VERSION.json",
    "desktop/src-tauri/tauri.conf.json",
    "desktop/src-tauri/Cargo.toml",
}
RELEASE_CONTROL_PREFIXES = ("config/release-trigger-",)

def changed_files(base: str, head: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=ROOT, text=True
    )
    return [line.strip() for line in out.splitlines() if line.strip()]

def is_product(path: str) -> bool:
    return path in PRODUCT_EXACT or path.startswith(PRODUCT_PREFIXES)

def is_release_control(path: str) -> bool:
    return path in RELEASE_CONTROL_EXACT or path.startswith(RELEASE_CONTROL_PREFIXES)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()
    changed = changed_files(args.base, args.head)
    product = sorted(p for p in changed if is_product(p))
    release = sorted(p for p in changed if is_release_control(p))
    if product and release:
        print("Change-boundary violation: product/runtime and release-control changes are mixed.")
        print("Product/runtime:")
        for p in product: print(f"  - {p}")
        print("Release control/version:")
        for p in release: print(f"  - {p}")
        print("Split this into a product PR and a separate release/process transaction.")
        return 1
    print(f"Change-boundary check passed ({len(changed)} changed files).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
