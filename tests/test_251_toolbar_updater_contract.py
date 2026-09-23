#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def main():
    docs = read("apps/documents/index.html")
    txt_template = read("apps/txt/page.template.html")
    txt_generated = read("apps/txt/index.html")
    canonical = (
        'd="M9 7 4 12l5 5"',
        'd="M5 12h8a6 6 0 0 1 6 6"',
        'd="m15 7 5 5-5 5"',
        'd="M19 12h-8a6 6 0 0 0-6 6"',
    )
    for token in canonical:
        assert token in docs, token
        assert token in txt_template, token
        assert token in txt_generated, token

    host = read("desktop/desktop-host.js")
    for drawer in ("generalMenu", "appDrawer", "moreMenu", "mainMenu"):
        assert f"'{drawer}'" in host
    assert "const menuList = drawer && drawer.querySelector('.menu-list');" in host
    assert "} else if (drawer && menuList) {" in host
    assert "menuList.append(button);" in host
    assert "drawer.append(button);" not in host

    css_files = (
        "apps/pdf/ui/pdf-toolbar.css",
        "apps/txt/runtime/frame/app-frame.css",
        "apps/epub/runtime/frame/app-frame.css",
    )
    for path in css_files:
        css = read(path)
        assert "InkDOS 2.5.1 toolbar visual normalization" in css, path
        assert "overflow-x:auto" in css, path
        assert "disabled" in css, path
    assert ".zoom-select{min-width:86px}" in read("apps/pdf/ui/pdf-toolbar.css")

    print("InkDOS 2.5.1 retained toolbar/updater contract passed.")


if __name__ == "__main__":
    main()
