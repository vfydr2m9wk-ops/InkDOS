from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(rel): return (ROOT / rel).read_text(encoding="utf-8")

def test_s9_hyperlink_command_is_guarded_and_does_not_rewrite_cell_payload():
    engine=read("apps/spreadsheets/engine/workbook-editor.js")
    controller=read("apps/spreadsheets/ui/editor-controller.js")
    chrome=read("apps/spreadsheets/ui/chrome-controller.js")
    html=read("apps/spreadsheets/index.html")
    body=engine.split("setHyperlink(target){",1)[1].split("removeHyperlink(){",1)[0]
    assert "/^(?:https?:|mailto:)/i" in body
    assert "cell.hyperlink={target,external:true}" in body
    assert ".v=" not in body and ".f=" not in body and ".t=" not in body
    assert "registerGuarded('insert.hyperlink','Hyperlink'" in controller
    assert "registerGuarded('remove.hyperlink','Hyperlink'" in controller
    assert "query.hyperlink" in controller and "linkBtn" in chrome
    assert 'id="linkBtn"' in html

def test_s9_xlsx_import_and_export_preserve_relationship_semantics():
    io=read("apps/spreadsheets/io/xlsx-engine.js")
    assert "localAll(doc,'hyperlink')" in io
    assert "sheetRelMap[rid]" in io
    assert "relationships/hyperlink" in io
    assert "TargetMode','External'" in io
    assert "patchHyperlinks(doc,sheet,rids)" in io
    assert "syncHyperlinkRelationships(zip,s)" in io
    assert "hyperlink:cell.hyperlink?JSON.parse(JSON.stringify(cell.hyperlink)):null" in io
    assert "JSON.stringify(a.hyperlink||null)===JSON.stringify(b.hyperlink||null)" in io
