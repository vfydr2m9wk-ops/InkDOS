from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(p): return (ROOT/p).read_text(encoding="utf-8")

def test_checklist_toolbar_and_command_wiring():
    html=read("apps/documents/index.html")
    commands=read("apps/documents/runtime/commands/document-commands.js")
    controller=read("apps/documents/ui/command-controller.js")
    assert 'id="checklistBtn"' in html and '☐≡' in html
    assert "register('format.checklist',()=>editor.toggleChecklist())" in commands
    assert "bindClick('checklistBtn','format.checklist')" in controller

def test_checklist_editor_is_local_and_roundtrip_text_safe():
    editor=read("apps/documents/ui/editor-controller.js")
    writer=read("apps/documents/io/docx-writer.js")
    assert 'function toggleChecklist()' in editor
    assert "mark.textContent='☐ '" in editor
    assert "mark.contentEditable='false'" in editor
    assert "b.dataset.checklist='1'" in editor
    # The base writer strips only list-label/search helpers, so checklist marker text is retained in DOCX output.
    assert "clone.querySelectorAll('.list-label,img,mark[data-search]')" in writer
    assert '.checklist-marker' not in writer.split("clone.querySelectorAll('.list-label,img,mark[data-search]')",1)[0][-120:]

def test_checklist_style_is_non_destructive():
    css=read("apps/documents/ui/editor.css")
    assert '.checklist-marker' in css
    assert '[data-checklist="1"]' in css
