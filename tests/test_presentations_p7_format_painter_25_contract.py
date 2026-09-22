from pathlib import Path
S=(Path(__file__).resolve().parents[1]/'apps/presentations/ui/ppt-p1-tools.js').read_text()
def test_p7_format_painter_is_direct_and_uses_style_bundle():
 assert "pptP1FormatPainter" in S and "function styleBundle" in S and "function applyBundle" in S
 assert "history.transact" in S and "Format painter" in S
def test_p7_does_not_copy_geometry_or_content():
 body=S[S.index('function styleBundle'):S.index('function applyTextColor')]
 assert 'o.x' not in body and 'o.y' not in body and 'o.text' not in body and 'src' not in body
