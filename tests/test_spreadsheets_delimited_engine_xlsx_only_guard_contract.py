#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def require(text, needle, label):
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')

def main():
    editor=(ROOT/'apps/spreadsheets/engine/workbook-editor.js').read_text(encoding='utf-8')
    require(editor, "isDelimited(){return this.session.sourceKind==='csv'||this.session.sourceKind==='tsv'}", 'central delimited predicate')
    require(editor, "formatSelection(mutator,label='Format cells'){if(this.isDelimited())return false;", 'engine formatting fail-closed guard')
    require(editor, "toggleMerge(){if(this.isDelimited())return false;", 'engine merge fail-closed guard')
    require(editor, "resizeColumn(c,width){if(this.isDelimited())return false;", 'engine column-width fail-closed guard')
    require(editor, "resizeRow(r,height){if(this.isDelimited())return false;", 'engine row-height fail-closed guard')
    for helper in ('toggleFont(key)', 'setAlignment(value)', 'setFont(name)', 'setFontSize(size)'):
        require(editor, helper, f'format helper {helper}')
    print('Spreadsheets CSV/TSV engine XLSX-only helper guard contract: OK')

if __name__=='__main__': main()
