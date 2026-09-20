from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / 'apps/spreadsheets/engine/workbook-editor.js').read_text(encoding='utf-8')

# Clear is a legal CSV/TSV mutation. It must erase content in place without
# reparsing/coercing the cell, so a delimited string cell remains t='s'.
match = re.search(r" clear\(\)\{(.*?)\n insertRow\(\)", SRC, re.S)
assert match, 'clear implementation missing'
body = match.group(1)
assert "cell.v=''" in body and "cell.f=''" in body and "cell.display=''" in body
assert 'cell.t=' not in body, 'clear must preserve the existing delimited cell type'
assert 'parseInput(' not in body and 'Number(' not in body, 'clear must not coerce delimited cells'

# Undo/redo snapshots must retain the full cell object (including t/f/v/display)
# rather than reconstructing cells from display values.
assert "cells:[...sheet.cells].map(([k,v])=>[k,cloneCell(v)])" in SRC
assert "sheet.cells=new Map(s.cells.map(([k,v])=>[k,cloneCell(v)]))" in SRC
assert "snap=direction==='undo'?action.before:action.after" in SRC
assert 'restoreSheet(s,snap)' in SRC

print('Spreadsheets CSV/TSV clear + undo/redo type preservation contract: OK')
