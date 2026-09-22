from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_font_family_toolbar_and_command_preserve_model_semantics():
    html=(ROOT/'apps/presentations/index.html').read_text()
    commands=(ROOT/'apps/presentations/ui/command-controller.js').read_text()
    editor=(ROOT/'apps/presentations/ui/editing-controller.js').read_text()
    writer=(ROOT/'apps/presentations/io/pptx-preservation-writer.js').read_text()
    assert 'id="fontFamily"' in html
    assert "register('format.fontFamily'" in commands
    assert 'o.fontFamily=v' in commands and 'r.fontFamily=v' in commands
    assert "family.dataset.command='format.fontFamily'" in editor
    assert "if(r.fontFamily)" in writer and "typeface" in writer
