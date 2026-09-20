from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / 'apps/spreadsheets/ui/editor-controller.js').read_text(encoding='utf-8')

# Selection statistics must honor spreadsheet semantic type. Numeric-looking text
# (including CSV/TSV-preserved text) and booleans must not be coerced into numbers.
assert "nums=vals.filter(v=>typeof v==='number'&&Number.isFinite(v))" in SRC
assert "nums=vals.map(Number).filter(Number.isFinite)" not in SRC
print('PASS spreadsheet selection stats semantic type preservation contract')
