from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_s2_toolbar_exposes_text_and_fill_color():
    h=text('apps/spreadsheets/index.html')
    assert 'id="textColorInput" type="color"' in h
    assert 'id="fillColorInput" type="color"' in h
    assert h.index('underlineBtn') < h.index('textColorInput') < h.index('fillColorInput') < h.index('alignmentSelect')
def test_s2_commands_are_guarded_and_style_only():
    c=text('apps/spreadsheets/ui/editor-controller.js'); e=text('apps/spreadsheets/engine/workbook-editor.js')
    assert "registerGuarded('format.textColor','Text color'" in c
    assert "registerGuarded('format.fillColor','Cell fill color'" in c
    assert "cell.style.font.color=String(color||'').trim()" in e
    assert "cell.style.fill=String(color||'').trim()" in e
    segment=e[e.index(' setTextColor'):e.index(' setNumberFormat')]
    assert '.v=' not in segment and '.f=' not in segment and '.t=' not in segment
def test_s2_xlsx_roundtrip_style_paths_exist():
    x=text('apps/spreadsheets/io/xlsx-engine.js')
    assert "color:argb(children(f,'color')[0]?.getAttribute('rgb')||'')" in x
    assert "fill:fillList[+(x.getAttribute('fillId')||0)]||''" in x
    assert "if(f.color){const c=create(doc,'color')" in x
    assert "pattern.setAttribute('patternType',st.fill?'solid':'none')" in x
