from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding="utf-8")
def test_s7_rotation_wiring_and_guard():
    html=text("apps/spreadsheets/index.html"); chrome=text("apps/spreadsheets/ui/chrome-controller.js"); ctl=text("apps/spreadsheets/ui/editor-controller.js"); eng=text("apps/spreadsheets/engine/workbook-editor.js")
    assert 'id="rotationSelect"' in html
    assert "commands.execute('format.rotation'" in chrome
    assert "registerGuarded('format.rotation','Text rotation'" in ctl
    assert "setRotation(value)" in eng and "rotation < -90||rotation > 90" in eng
def test_s7_roundtrip_and_renderer_contract():
    x=text("apps/spreadsheets/io/xlsx-engine.js"); grid=text("apps/spreadsheets/view/grid-surface.js")
    assert "textRotation" in x and "rotation:+(al?.getAttribute('textRotation')||0)" in x
    assert "st.rotation<0?180+st.rotation:st.rotation" in x
    assert "rotate(${st.rotation>90?st.rotation-180:st.rotation}deg)" in grid
def test_run18_settings_no_checkmark_durability():
    for rel in ["shared/settings.js","index.html"]:
        p=ROOT/rel
        if p.exists():
            s=p.read_text(encoding="utf-8")
            assert "✓" not in s and "✔" not in s
