from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_s11_filter_sort_commands_and_ui():
    html=text('apps/spreadsheets/index.html'); chrome=text('apps/spreadsheets/ui/chrome-controller.js'); ctl=text('apps/spreadsheets/ui/editor-controller.js'); eng=text('apps/spreadsheets/engine/workbook-editor.js')
    for id_ in ['filterBtn','sortAscBtn','sortDescBtn']: assert f'id="{id_}"' in html
    assert "commands.execute('data.filter')" in chrome and "commands.execute('data.sort','asc')" in chrome and "commands.execute('data.sort','desc')" in chrome
    assert "registerGuarded('data.filter','Filter'" in ctl and "registerGuarded('data.sort','Sort'" in ctl
    assert 'toggleFilter()' in eng and "sortSelection(direction='asc')" in eng
def test_s11_preservation_safeguards_and_roundtrip():
    eng=text('apps/spreadsheets/engine/workbook-editor.js'); x=text('apps/spreadsheets/io/xlsx-engine.js')
    assert 'if(this.isDelimited())return false' in eng
    assert 'if(s.cells.get(this.ref(r,c))?.f)return false' in eng
    assert '(s.merges||[]).some' in eng and '(s.tables||[]).some' in eng
    assert 'cloneCell(s.cells.get(this.ref(r,c))||null)' in eng
    assert 'originalAutoFilter' in x and 'function patchAutoFilter(doc,sheet)' in x
    assert "String(sheet.originalAutoFilter||'')!==String(sheet.autoFilter||'')" in x
def test_run18_no_checkmark_in_settings_surfaces():
    for rel in ['shared/settings.js','index.html']:
        p=ROOT/rel
        if p.exists():
            s=p.read_text(encoding='utf-8'); assert '✓' not in s and '✔' not in s
