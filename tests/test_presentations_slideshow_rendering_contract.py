#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOW = (ROOT / 'apps/presentations/presentation/slideshow-controller.js').read_text(encoding='utf-8')
COLUMNS = (ROOT / 'apps/presentations/io/pptx-text-columns.js').read_text(encoding='utf-8')

# Slideshow geometry must scale the intrinsic slide as one unit. Font metrics
# therefore remain in the same px/pt coordinate system used by the editor and
# must never be tied directly to viewport height.
assert "const NS=global.InkDOS2Presentations=global.InkDOS2Presentations||{},EMU=12700" in SHOW
assert "line.style.fontSize=linePt+'px'" in SHOW
assert "s.style.fontSize=((r.fontSizePt||o.fontSizePt||24)*(o.autoFitScale||1))+'px'" in SHOW
assert "+'vh'" not in SHOW, 'Slideshow text sizing regressed to viewport-height units.'
assert "frame.style.transform=`scale(${scale})`" in SHOW
assert "overlay?.clientWidth" in SHOW and "overlay?.clientHeight" in SHOW
assert "global.visualViewport?.addEventListener?.('resize',fitCurrent)" in SHOW

# Paint semantics must match editor behavior for the known fidelity-sensitive
# object features: opacity, crop, line width, rounded shapes, and tables.
assert "el.style.opacity=String(o.opacity??1)" in SHOW
assert "const c=o.crop||{}" in SHOW
assert "img.style.width=(100/vw)+'%'" in SHOW
assert "img.style.left=(-l/vw*100)+'%'" in SHOW
assert "return `${Math.max(1,px(line.widthEmu||12700))}px solid ${line.color}`" in SHOW
assert "o.shapeType==='roundRect'" in SHOW
assert "o.type==='table'" in SHOW and "function tableNode(o)" in SHOW
assert "Number(r.charSpacingPt)" in SHOW
assert "p.spaceBeforePt" in SHOW and "p.spaceAfterPt" in SHOW

# Text-column enrichment must follow the nested intrinsic slideshow layer and
# target objects by stable object id rather than by incidental child order.
assert "[data-slideshow-layer]" in COLUMNS
assert "CSS.escape(object.id)" in COLUMNS
assert "[data-slideshow-text-content]" in COLUMNS

print('Presentations slideshow intrinsic-scale and paint-parity contract passed.')
