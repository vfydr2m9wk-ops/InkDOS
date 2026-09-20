from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / 'apps/spreadsheets/engine/workbook-editor.js').read_text(encoding='utf-8')

# Engine-level fail-safe: CSV/TSV commits must remain literal text even when a
# caller bypasses the UI conversion guard. XLSX still reaches formula parsing.
needle = "function parseInput(value,preserveText=false){value=String(value??'');if(preserveText)return{v:value,f:'',t:'s',display:value};if(value.startsWith('='))return{v:'',f:value.slice(1),t:'n',display:value};"
assert needle in SRC, 'Delimited text preservation must precede formula parsing'
assert "preserveText=this.session.sourceKind==='csv'||this.session.sourceKind==='tsv',parsed=parseInput(value,preserveText)" in SRC
print('Spreadsheets CSV/TSV engine-level formula text-preservation contract: OK')
