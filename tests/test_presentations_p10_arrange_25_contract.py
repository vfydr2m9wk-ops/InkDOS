from pathlib import Path
S=(Path(__file__).resolve().parents[1]/'apps/presentations/ui/ppt-p1-tools.js').read_text()
def test_arrange_exposes_order_and_align_to_slide():
 assert "pptP1Arrange" in S
 for x in ['Bring forward','Send backward','Bring to front','Send to back','Align left','Align center','Align right','Align top','Align middle','Align bottom']: assert x in S
def test_imported_pptx_z_order_is_fail_closed_but_geometry_alignment_is_safe():
 assert "session.sourceKind==='pptx'" in S
 assert 'stacking changes are preserve-only for imported PPTX' in S
 assert "transact('Align object'" in S
