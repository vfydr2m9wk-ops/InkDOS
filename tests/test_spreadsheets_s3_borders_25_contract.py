from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def test_s3_border_command_and_guard():
    e=read('apps/spreadsheets/engine/workbook-editor.js'); c=read('apps/spreadsheets/ui/editor-controller.js'); u=read('apps/spreadsheets/ui/chrome-controller.js')
    assert 'setBorders(' in e
    assert "registerGuarded('format.borders','Cell borders'" in c
    assert "commands.execute('format.borders'" in u
    assert "if(this.isDelimited())return false" in e

def test_s3_toolbar_exposes_sides_style_width_color():
    h=read('apps/spreadsheets/index.html')
    for token in ['borderSides','borderStyle','borderWidth','borderColorInput']:
        assert f'id="{token}"' in h

def test_s3_roundtrip_uses_existing_xlsx_border_model():
    x=read('apps/spreadsheets/io/xlsx-engine.js'); v=read('apps/spreadsheets/view/grid-surface.js')
    assert "for(const sideName of['left','right','top','bottom'])" in x
    assert "st.border?.[sideName]" in x
    assert "for(const side of['left','right','top','bottom'])" in v
