from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'apps/presentations/ui/ppt-p1-tools.js').read_text()
def test_p12_base_order_and_missing_surfaces():
    order=['addSlideBtn','undoBtn','redoBtn','pptP1PrintBtn','pptP1FormatPainter','zoomMenuBtn','pptP1SelectBtn','insertTextBtn','pptP1ImageBtn','pptP1Shape','pptP1LineBtn','pptP2CommentBtn','pptP1Background','pptP1Layout','pptP2ThemeBtn','pptP2Transition']
    positions=[s.index("'"+x+"'") for x in order]
    assert positions==sorted(positions)
    assert "global.print()" in s and "selection.clear()" in s
def test_p12_context_groups():
    assert "textGroup.hidden=!(safe&&o.type==='text')" in s
    assert "styleGroup.hidden=!safe" in s
    for x in ['pptP1Fill','pptP1Border','pptP1BorderWidth','pptP1BorderStyle','pptP1Arrange']:
        assert x in s
