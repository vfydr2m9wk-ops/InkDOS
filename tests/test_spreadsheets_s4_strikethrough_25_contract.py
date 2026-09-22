from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding="utf-8")
def test_s4_strike_command_guard_and_toolbar():
    h=read("apps/spreadsheets/index.html"); c=read("apps/spreadsheets/ui/editor-controller.js"); u=read("apps/spreadsheets/ui/chrome-controller.js")
    assert 'id="strikeBtn"' in h
    assert "registerGuarded('format.strike','Strikethrough formatting',()=>editor.toggleFont('strike'))" in c
    assert "commands.execute('format.strike')" in u
    assert "!!font.strike" in u
def test_s4_reuses_existing_style_and_roundtrip_semantics():
    e=read("apps/spreadsheets/engine/workbook-editor.js"); x=read("apps/spreadsheets/io/xlsx-engine.js"); v=read("apps/spreadsheets/view/grid-surface.js")
    assert "cell.style.font[key]=!cell.style.font[key]" in e
    assert "if(f.strike)font.appendChild(create(doc,'strike'))" in x
    assert "if(f.strike)dec.push('line-through')" in v
