from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def text(rel): return (ROOT/rel).read_text(encoding='utf-8')

def test_s1_toolbar_order_and_controls():
    html=text('apps/spreadsheets/index.html')
    ids=['undoBtn','redoBtn','zoomMenuBtn','currencyBtn','percentBtn','decreaseDecimalsBtn','increaseDecimalsBtn','numberFormat','fontFamily']
    pos=[html.index(f'id="{x}"') for x in ids]
    assert pos==sorted(pos)
    assert '<option value="general">General</option>' in html
    assert '<option value="number">Number</option>' in html
    assert '<option value="currency">Currency</option>' in html
    assert '<option value="percent">Percent</option>' in html

def test_s1_commands_format_without_mutating_values():
    editor=text('apps/spreadsheets/engine/workbook-editor.js')
    controller=text('apps/spreadsheets/ui/editor-controller.js')
    assert "setNumberFormat(kind)" in editor
    assert "adjustDecimals(delta)" in editor
    assert "cell.style.numFmtId=preset.numFmtId" in editor
    assert "cell.style.numberFormat=preset.numberFormat" in editor
    assert "registerGuarded('format.number'" in controller
    assert "registerGuarded('format.decimals'" in controller
    block=editor[editor.index(' setNumberFormat(kind)'):editor.index(' toggleMerge()',editor.index(' setNumberFormat(kind)'))]
    assert 'cell.v=' not in block and 'cell.f=' not in block

def test_s1_display_uses_style_and_roundtrip_ids_are_builtin_safe():
    grid=text('apps/spreadsheets/view/grid-surface.js')
    xlsx=text('apps/spreadsheets/io/xlsx-engine.js')
    assert 'function formattedNumber(value,style)' in grid
    assert "fmt.includes('%')" in grid
    assert 'numFmtId' in xlsx and 'applyNumberFormat' in xlsx
    editor=text('apps/spreadsheets/engine/workbook-editor.js')
    for frag in ["numFmtId:4","numFmtId:7","numFmtId:10","st.numFmtId=decimals?10:9","st.numFmtId=decimals?7:5","st.numFmtId=decimals?4:3"]:
        assert frag in editor
