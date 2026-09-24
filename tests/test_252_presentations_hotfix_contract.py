#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def main():
    css = read("apps/presentations/ui/editor.css")
    assert "InkDOS 2.5.1 toolbar visual normalization — presentation only" not in css
    assert ".tool-btn,.editbar select{height:var(--control);min-width:var(--control);border:1px solid transparent;border-radius:8px;background:transparent;cursor:pointer}" in css
    assert ".tool-btn.icon-only{width:var(--control);padding:0;display:grid;place-items:center}" in css
    assert "@media(max-width:720px){.tool-label{display:none}.tool-btn.labeled-tool{width:var(--control);padding:0}" in css

    surface = read("apps/presentations/view/presentation-surface.css")
    zoom = read("apps/presentations/view/zoom-controller.js")
    app = read("apps/presentations/app.js")
    assert ".content-viewport{min-width:0;min-height:0;overflow:auto" in surface
    assert ".slide-stage{position:relative;min-width:100%;min-height:100%}" in surface
    assert ".slide-shell{position:absolute;left:0;top:0}" in surface
    assert ".slide-canvas{position:absolute;left:0;top:0;transform-origin:0 0" in surface
    assert "this.shell.style.left=Math.max(0,(stageW-policy.width)/2)+'px'" in zoom
    assert "this.shell.style.top=Math.max(0,(stageH-policy.height)/2)+'px'" in zoom
    assert "surface.render();panel.render();zoom.recenter()" in app

    print("InkDOS 2.5.2 Presentations rollback geometry contract passed.")

if __name__ == "__main__":
    main()
