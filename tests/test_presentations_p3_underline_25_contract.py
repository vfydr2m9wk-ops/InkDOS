from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_underline_toolbar_command_and_pptx_writer_contract():
    html=(ROOT/'apps/presentations/index.html').read_text(); commands=(ROOT/'apps/presentations/ui/command-controller.js').read_text(); editor=(ROOT/'apps/presentations/ui/editing-controller.js').read_text(); writer=(ROOT/'apps/presentations/io/pptx-preservation-writer.js').read_text()
    assert 'id="underlineBtn"' in html
    assert "register('format.underline'" in commands and 'r.underline=o.underline' in commands
    assert "bindClick('underlineBtn','format.underline')" in editor
    assert "if(r.underline)rp.setAttribute('u','sng')" in writer
