from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def test_s13_conventional_primary_order():
    s=read('apps/spreadsheets/index.html')
    ids=['undoBtn','redoBtn','printBtn','formatPainterBtn','zoomMenuBtn','currencyBtn','percentBtn','decreaseDecimalsBtn','increaseDecimalsBtn','numberFormat','fontFamily','fontSize','boldBtn','italicBtn','underlineBtn','strikeBtn','textColorInput','fillColorInput','borderSides','mergeBtn','alignmentSelect','verticalAlignmentSelect','wrapSelect','rotationSelect','linkBtn','commentBtn','chartBtn','filterBtn','operationSelect']
    positions=[s.index(f'id="{x}"') for x in ids]
    assert positions==sorted(positions)
def test_s13_print_and_structural_tail():
    html=read('apps/spreadsheets/index.html'); chrome=read('apps/spreadsheets/ui/chrome-controller.js')
    assert "on('printBtn','click',()=>root.print())" in chrome
    assert html.index('id="operationSelect"') < html.index('id="addRowBtn"')
    assert html.index('id="addRowBtn"') < html.index('class="toolbar-end-spacer"')
def test_s13_preserves_horizontal_rail():
    css=read('apps/spreadsheets/ui/editor-toolbar.css')
    assert '.command-scroll{overflow-x:auto' in css
