from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_shape_and_line_are_clear_separate_insert_tools_using_same_object_engine():
    js=(ROOT/'apps/presentations/ui/ppt-p1-tools.js').read_text()
    assert "button('pptP1LineBtn','Insert line','Line')" in js
    assert "line.onclick=()=>insertShape('line')" in js
    assert "insert.append(image,shape,line)" in js
    assert '<option value="line">Line</option>' not in js
    assert "session.addShape(value)" in js
