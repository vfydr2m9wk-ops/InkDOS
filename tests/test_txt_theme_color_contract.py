#!/usr/bin/env python3
"""Plain Text uses the same light theme-color as the other workspaces (audit V14)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "#f7f8fa"


def main():
    manifest = json.loads((ROOT / "apps/txt/manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["theme_color"] == EXPECTED, manifest["theme_color"]
    assert manifest["background_color"] == EXPECTED, manifest["background_color"]
    for rel in ("apps/txt/page.template.html", "apps/txt/index.html"):
        html = (ROOT / rel).read_text(encoding="utf-8")
        assert f'<meta name="theme-color" content="{EXPECTED}">' in html, rel
    print("TXT theme-color contract: OK")


if __name__ == "__main__":
    main()
