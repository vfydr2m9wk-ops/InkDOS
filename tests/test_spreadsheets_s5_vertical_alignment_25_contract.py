from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def test_s5_toolbar_command_and_existing_style_model():
    html=read('apps/spreadsheets/index.html'); chrome=read('apps/spreadsheets/ui/chrome-controller.js'); controller=read('apps/spreadsheets/ui/editor-controller.js'); editor=read('apps/spreadsheets/engine/workbook-editor.js')
    assert 'id="verticalAlignmentSelect"' in html
    assert "format.verticalAlignment" in controller and "setVerticalAlignment" in editor
    assert "commands.execute('format.verticalAlignment',value)" in chrome
    assert "cell.style.vertical=value" in editor
    assert "['top','center','bottom'].includes(value)" in editor
def test_s5_render_and_xlsx_round_trip_paths_remain_native():
    grid=read('apps/spreadsheets/view/grid-surface.js'); xlsx=read('apps/spreadsheets/io/xlsx-engine.js')
    assert "st.vertical==='top'" in grid and "st.vertical==='bottom'" in grid and "st.vertical==='center'" in grid
    assert "vertical:al?.getAttribute('vertical')||''" in xlsx
    assert "vertical:st.vertical||''" in xlsx
