#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ZOOM=(ROOT/"apps/presentations/view/zoom-controller.js").read_text(encoding="utf-8")
assert "/AppleWebKit/i.test(navigator.userAgent||'')" in ZOOM
assert "navigator.maxTouchPoints" in ZOOM
assert "CSS?.supports?.('zoom','1')" in ZOOM
assert "this.canvas.style.zoom=String(policy.scale)" in ZOOM
assert "this.canvas.style.transform='none'" in ZOOM
assert "this.canvas.style.zoom=''" in ZOOM
assert "this.canvas.style.transform='scale('+policy.scale+')'" in ZOOM
print("Presentations 2.5.2 touch-WebKit zoom fallback contract passed.")
