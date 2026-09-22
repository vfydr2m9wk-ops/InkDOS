from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_docx_parser_resolves_external_hyperlink_relationships():
    s=(ROOT/'apps/documents/engine/docx-parser.js').read_text(encoding='utf-8')
    assert "data-docx-href" in s
    assert "rels&&rels[attr(child,'id')]" in s
    assert "safeHref" in s

def test_docx_writer_extension_emits_external_hyperlink_relationships():
    s=(ROOT/'apps/documents/engine/d2-docx-extension.js').read_text(encoding='utf-8')
    for needle in ["relationships/hyperlink", "TargetMode','External", "<w:hyperlink r:id=", "writeHyperlinks(zip,root,ctx.links)"]:
        assert needle in s
    assert "a[href],[data-docx-href]" in s


def test_d2_toolbar_exposes_insert_edit_remove_hyperlink_action():
    html=(ROOT/'apps/documents/index.html').read_text(encoding='utf-8')
    commands=(ROOT/'apps/documents/runtime/commands/document-commands.js').read_text(encoding='utf-8')
    controller=(ROOT/'apps/documents/ui/command-controller.js').read_text(encoding='utf-8')
    editor=(ROOT/'apps/documents/ui/editor-controller.js').read_text(encoding='utf-8')
    assert 'id="hyperlinkBtn"' in html
    assert "register('insert.hyperlink',()=>editor.editHyperlink())" in commands
    assert "bindClick('hyperlinkBtn','insert.hyperlink')" in controller
    for needle in ["function editHyperlink()", "document.execCommand('createLink'", "Hyperlink removed", "data-docx-href"]:
        assert needle in editor

def test_hyperlink_paragraphs_force_rich_serializer_path():
    s=(ROOT/'apps/documents/engine/d2-docx-extension.js').read_text(encoding='utf-8')
    assert "[data-d2-comment-id],[data-d2-footnote-id],a[href],[data-docx-href]" in s
