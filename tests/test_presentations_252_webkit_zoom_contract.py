#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ZOOM=(ROOT/"apps/presentations/view/zoom-controller.js").read_text(encoding="utf-8")
assert "translateZ(0) scale(" in ZOOM
assert "this.canvas.style.transform=transform" in ZOOM
assert "this.canvas.style.webkitTransform=transform" in ZOOM
assert "this.canvas.style.backfaceVisibility='hidden'" in ZOOM
assert "this.canvas.style.webkitBackfaceVisibility='hidden'" in ZOOM
assert "this.canvas.style.willChange='transform'" in ZOOM
assert "this.canvas.style.zoom=''" in ZOOM
print("Presentations 2.5.2 WebKit compositing contract passed.")
