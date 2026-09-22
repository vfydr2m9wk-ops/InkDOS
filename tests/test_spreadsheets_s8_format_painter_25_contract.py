from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel): return (ROOT / rel).read_text(encoding="utf-8")

def test_s8_format_painter_uses_complete_style_bundle_and_two_step_state():
    engine = read("apps/spreadsheets/engine/workbook-editor.js")
    controller = read("apps/spreadsheets/ui/editor-controller.js")
    chrome = read("apps/spreadsheets/ui/chrome-controller.js")
    html = read("apps/spreadsheets/index.html")
    assert "this.formatPainterStyle=null" in engine
    assert "this.formatPainterStyle=clone(cell?.style||{})" in engine
    assert "cell.style=clone(style)" in engine
    assert "toggleFormatPainter()" in engine
    assert "registerGuarded('format.painter','Format painter'" in controller
    assert "formatPainterArmed:editor.isFormatPainterArmed()" in controller
    assert "formatPainterBtn" in chrome and "aria-pressed" in chrome
    assert 'id="formatPainterBtn"' in html

def test_s8_format_painter_preserves_values_formulas_and_delimited_guard():
    engine = read("apps/spreadsheets/engine/workbook-editor.js")
    controller = read("apps/spreadsheets/ui/editor-controller.js")
    apply = engine.split("applyCapturedFormat(){",1)[1].split("toggleFormatPainter(){",1)[0]
    assert ".v=" not in apply and ".f=" not in apply and ".t=" not in apply
    assert "formatSelection" in apply
    assert "registerGuarded('format.painter'" in controller
