from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_s10_comment_model_ui_and_guard():
    html=text('apps/spreadsheets/index.html'); chrome=text('apps/spreadsheets/ui/chrome-controller.js'); ctl=text('apps/spreadsheets/ui/editor-controller.js'); eng=text('apps/spreadsheets/engine/workbook-editor.js')
    assert 'id="commentBtn"' in html
    assert "commands.execute('query.comment')" in chrome and "'insert.comment'" in chrome and "'remove.comment'" in chrome
    assert "registerGuarded('insert.comment','Cell comment'" in ctl and "registerGuarded('remove.comment','Cell comment'" in ctl
    assert 'setComment(text)' in eng and 'removeComment()' in eng and 'activeComment()' in eng
def test_s10_xlsx_comment_roundtrip_contract():
    x=text('apps/spreadsheets/io/xlsx-engine.js')
    assert 'comment:cell.comment?JSON.parse(JSON.stringify(cell.comment)):null' in x
    assert "commentsRel=Object.values(sheetRelMap).find" in x
    assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.comments+xml' in x
    assert 'relationships/comments' in x and '<comment ref=' in x
    assert "JSON.stringify(a.comment||null)" in x
def test_run18_no_checkmark_in_settings_surfaces():
    for rel in ['shared/settings.js','index.html']:
        p=ROOT/rel
        if p.exists():
            s=p.read_text(encoding='utf-8'); assert '✓' not in s and '✔' not in s
def test_s10_imported_workbook_comment_parts_are_synchronized():
    x=text('apps/spreadsheets/io/xlsx-engine.js')
    assert 'async function syncCommentParts(zip,sheet)' in x
    assert 'commentPartXml(comments)' in x and 'commentVmlXml(comments)' in x
    assert "endsWith('/vmlDrawing')" in x
    assert "ensureCommentContentType(zip,commentPath,true)" in x
    assert 'legacyDrawingRid=await syncCommentParts(zip,s)' in x
    assert 'patchLegacyDrawing(doc,legacyDrawingRid)' in x
