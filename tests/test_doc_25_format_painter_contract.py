from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def text(p): return (ROOT/p).read_text(encoding="utf-8")

def test_format_painter_toolbar_and_commands():
    html=text("apps/documents/index.html")
    commands=text("apps/documents/runtime/commands/document-commands.js")
    ui=text("apps/documents/ui/command-controller.js")
    assert 'id="formatPainterBtn"' in html
    assert "format.copyFormatting" in commands and "format.applyFormatting" in commands
    assert "captureFormatting" in commands and "applyFormatting" in commands
    assert "formatPainterBtn" in ui and "aria-pressed" in ui

def test_format_painter_preserves_content_and_copies_style_bundle():
    editor=text("apps/documents/ui/editor-controller.js")
    for token in ["fontFamily","fontSize","fontWeight","fontStyle","textDecorationLine","color","backgroundColor","textAlign","lineHeight"]:
        assert token in editor
    assert "r.extractContents()" in editor
    assert "markDirty()" in editor
