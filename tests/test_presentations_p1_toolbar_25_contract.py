from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_p1_uses_explicit_host_groups_and_conventional_group_order():
    html=(ROOT/'apps/presentations/index.html').read_text()
    js=(ROOT/'apps/presentations/ui/ppt-p1-tools.js').read_text()
    for ident in ['pptToolbarSlides','pptToolbarHistory','pptToolbarView','pptToolbarInsert','pptToolbarText','pptToolbarObjectStyle']:
        assert f'id="{ident}"' in html
    assert "for(const group of [base,text,style,secondary])" in js
    assert "bar.insertBefore(group,spacer)" in js
    assert "textGroup.hidden=!(safe&&o.type==='text')" in js
    assert "styleGroup.hidden=!safe" in js
    assert "'moveSlideUpBtn','moveSlideDownBtn'" in js
