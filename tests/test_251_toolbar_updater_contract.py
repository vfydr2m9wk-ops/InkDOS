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
        "apps/presentations/ui/editor.css",
        "apps/pdf/ui/pdf-toolbar.css",
        "apps/txt/runtime/frame/app-frame.css",
        "apps/epub/runtime/frame/app-frame.css",
    )
    for path in css_files:
        css = read(path)
        assert "InkDOS 2.5.1 toolbar visual normalization" in css, path
        assert "overflow-x:auto" in css, path
        assert "disabled" in css, path
    assert ".tool-btn.zoom-tool{min-width:82px}" in read("apps/presentations/ui/editor.css")
    assert ".zoom-select{min-width:86px}" in read("apps/pdf/ui/pdf-toolbar.css")

    meta = json.loads(read("VERSION.json"))
    assert meta["version"] == "2.5.1"
    assert meta["releaseName"] == "InkDOS 2.5.1"
    assert json.loads(read("desktop/src-tauri/tauri.conf.json"))["version"] == "2.5.1"
    assert 'version = "2.5.1"' in read("desktop/src-tauri/Cargo.toml")
    home = read("index.html")
    for app in ("documents","spreadsheets","presentations","pdf","txt","epub"):
        assert f"./apps/{app}/index.html?v=2.5.1&amp;suite=1" in home
    assert "inkdos-v2.5.1-" in read("service-worker.js")
    print("InkDOS 2.5.1 toolbar/updater/version contract passed.")

if __name__ == "__main__":
    main()
