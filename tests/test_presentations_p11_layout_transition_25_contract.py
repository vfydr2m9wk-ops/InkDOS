from pathlib import Path
S=(Path(__file__).resolve().parents[1]/'apps/presentations/ui/ppt-p2-tools.js').read_text()
def test_layout_and_transition_are_consolidated_in_slide_group():
 assert "document.getElementById('pptP1Layout')||document.getElementById('deleteSlideBtn')" in S
 assert "group.insertBefore(select,anchor.nextSibling)" in S
