from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p): return (ROOT/p).read_text(encoding='utf-8')
def test_chart_command_and_safe_source_guard():
 s=text('apps/spreadsheets/engine/workbook-editor.js')
 assert "addChart(type='barChart')" in s
 assert "this.session.book?.zip" in s
 assert "kind:'chart'" in s and "categoryFormula" in s and "valueFormula" in s
 assert "registerGuarded('insert.chart','Chart'" in text('apps/spreadsheets/ui/editor-controller.js')
def test_chart_ui_and_rendering():
 assert 'id="chartBtn"' in text('apps/spreadsheets/index.html')
 v=text('apps/spreadsheets/view/grid-surface.js')
 assert "drawing.kind==='chart'" in v and "chart-preview" in v
def test_new_xlsx_chart_package_export():
 s=text('apps/spreadsheets/io/xlsx-engine.js')
 assert "type:'chart'" in s
 assert 'drawingml.chart+xml' in s
 assert "for(const c of d.charts||[])zip.file(c.path,c.xml)" in s
 assert "relationships/${x.type||'image'}" in s
