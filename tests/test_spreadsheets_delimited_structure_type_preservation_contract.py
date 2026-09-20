from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / 'apps/spreadsheets/engine/workbook-editor.js').read_text(encoding='utf-8')

# CSV/TSV structural edits may move/delete cells, but must not reinterpret their
# values or types. Insert/delete rows/columns therefore move the existing cell
# object verbatim instead of reparsing values through parseInput/Number.
for method, expected in {
    'insertRow': "next.set(this.ref(p.r>=at?p.r+1:p.r,p.c),cell)",
    'insertColumn': "next.set(this.ref(p.r,p.c>=at?p.c+1:p.c),cell)",
    'deleteRows': "next.set(this.ref(p.r-count,p.c),cell)",
    'deleteColumns': "next.set(this.ref(p.r,p.c-count),cell)",
}.items():
    match = re.search(rf" {method}\(\)\{{(.*?)(?=\n [a-zA-Z].*?\(.*?\)\{{|\n\}})", SRC, re.S)
    assert match, f'{method} implementation missing'
    body = match.group(1)
    assert expected in body, f'{method} must move the original cell object without coercion'
    assert 'parseInput(' not in body, f'{method} must not reparse delimited cell values'
    assert 'Number(cell' not in body and 'Number(raw' not in body, f'{method} must not numerically coerce cells'

# Literal formula-looking text is protected by the same invariant because the
# cell object (including t='s' and f='') is moved unchanged.
assert "if(p.r<from)next.set(k,cell)" in SRC
assert "if(p.c<from)next.set(k,cell)" in SRC
print('Spreadsheets CSV/TSV structural-edit type preservation contract: OK')
