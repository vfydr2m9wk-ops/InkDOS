#!/usr/bin/env python3
"""Deterministically build the self-contained Plain Text distribution entry point."""
from __future__ import annotations

from pathlib import Path
import argparse
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "apps/txt/page.template.html"
OUTPUT = ROOT / "apps/txt/index.html"
STYLE_SOURCES = (
    "apps/txt/runtime/tokens/base.css",
    "apps/txt/styles.css",
    "apps/txt/runtime/frame/app-frame.css",
)
SCRIPT_MARKER = re.compile(r"<!-- SCRIPT ([^ ]+) -->")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def build() -> str:
    page = TEMPLATE.read_text(encoding="utf-8")
    styles = "\n\n".join(read(path).rstrip("\n") for path in STYLE_SOURCES)
    marker = "<!-- STYLES -->"
    if page.count(marker) != 1:
        raise SystemExit(f"Expected exactly one {marker} marker")
    page = page.replace(marker, f"<style>{styles}</style>")

    declared = SCRIPT_MARKER.findall(page)
    if not declared:
        raise SystemExit("Plain Text template declares no script modules")

    def inline_script(match: re.Match[str]) -> str:
        path = match.group(1)
        source = read(path).rstrip("\n")
        return f"<script>/* {path} */\n{source}\n</script>"

    page = SCRIPT_MARKER.sub(inline_script, page)
    if "<!-- SCRIPT " in page or "<!-- STYLES -->" in page:
        raise SystemExit("Unexpanded Plain Text bundle marker remains")
    return page


def first_difference(a: str, b: str) -> int | None:
    limit = min(len(a), len(b))
    for index in range(limit):
        if a[index] != b[index]:
            return index
    return None if len(a) == len(b) else limit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify index.html matches the deterministic build")
    args = parser.parse_args()
    generated = build()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8")
        if current != generated:
            offset = first_difference(current, generated)
            print(
                f"Plain Text bundle is stale: current={len(current)} generated={len(generated)} first_difference={offset}",
                file=sys.stderr,
            )
            raise SystemExit(1)
        print("Plain Text bundle matches deterministic source build.")
        return
    OUTPUT.write_text(generated, encoding="utf-8")
    print(f"Built {OUTPUT.relative_to(ROOT)} ({len(generated.encode('utf-8'))} bytes).")


if __name__ == "__main__":
    main()
