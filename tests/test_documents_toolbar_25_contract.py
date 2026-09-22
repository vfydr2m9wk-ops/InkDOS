from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_clear_formatting_is_direct_toolbar_action_and_registered():
    html=(ROOT/'apps/documents/index.html').read_text()
    commands=(ROOT/'apps/documents/runtime/commands/document-commands.js').read_text()
    controller=(ROOT/'apps/documents/ui/command-controller.js').read_text()
    editor=(ROOT/'apps/documents/ui/editor-controller.js').read_text()
    assert 'id="clearFormattingBtn"' in html
    assert 'title="Clear formatting"' in html
    assert "register('format.clear',()=>editor.clearFormatting())" in commands
    assert "bindClick('clearFormattingBtn','format.clear')" in controller
    assert "document.execCommand('removeFormat'" in editor
    assert "document.execCommand('unlink'" in editor

def test_clear_formatting_stays_before_structural_insert_tools():
    html=(ROOT/'apps/documents/index.html').read_text()
    assert html.index('id="clearFormattingBtn"') < html.index('id="tableBtn"')
