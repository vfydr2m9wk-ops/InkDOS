from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_s6_wrap_toolbar_and_command():
    html=text('apps/spreadsheets/index.html'); ui=text('apps/spreadsheets/ui/chrome-controller.js'); ctl=text('apps/spreadsheets/ui/editor-controller.js'); eng=text('apps/spreadsheets/engine/workbook-editor.js')
    assert 'id="wrapSelect"' in html and 'value="wrap"' in html and 'value="nowrap"' in html
    assert "commands.execute('format.wrap'" in ui
    assert "registerGuarded('format.wrap','Text wrapping'" in ctl
    assert "setWrap(value)" in eng and "cell.style.wrap=value==='wrap'" in eng
def test_s6_existing_roundtrip_and_renderer_are_reused():
    xlsx=text('apps/spreadsheets/io/xlsx-engine.js'); xls=text('apps/spreadsheets/io/xls-biff8-engine.js'); grid=text('apps/spreadsheets/view/grid-surface.js'); css=text('apps/spreadsheets/view/grid-surface.css')
    assert "wrapText:st.wrap?'1':''" in xlsx and "wrap:al?.getAttribute('wrapText')==='1'" in xlsx
    assert 'wrap:!!(a&8)' in xls
    assert "if(st.wrap)el.dataset.wrap='1'" in grid and '.cell[data-wrap="1"]' in css
def test_run18_settings_selected_rows_have_no_checkmark_glyph():
    shared=text('shared/localization/localization.css'); home=text('assets/home.css')
    assert ".inkdos-settings-option.active::after" not in shared
    assert 'button[aria-checked="true"]::after' not in home
    assert 'padding:0 30px 0 10px' not in home
