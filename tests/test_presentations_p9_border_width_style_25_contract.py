from pathlib import Path
R=Path(__file__).resolve().parents[1]
OPEN=(R/'apps/presentations/io/pptx-open-controller.js').read_text(); WRITE=(R/'apps/presentations/io/ppt-p1-object-writer.js').read_text(); UI=(R/'apps/presentations/ui/ppt-p1-tools.js').read_text(); VIEW=(R/'apps/presentations/view/slide-surface.js').read_text()
def test_border_width_and_style_are_direct_controls():
 assert "pptP1BorderWidth" in UI and "pptP1BorderStyle" in UI
 assert "function applyBorderWidth" in UI and "function applyBorderStyle" in UI
def test_pptx_line_style_roundtrips():
 assert "child(ln,'prstDash')" in OPEN
 assert "a:prstDash" in WRITE and "line.style" in WRITE
 assert "line.style==='dash'" in VIEW
