#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'apps/spreadsheets/ui/editor-controller.js').read_text(encoding='utf-8')

def main():
    needle="if(isDelimited()){const text=String(value);cell.v=text;cell.f='';cell.t='s';cell.display=text}else{cell.v=value;cell.f='';cell.t='n';cell.display=numericDisplay(value,cell)}"
    if needle not in SRC:
        raise AssertionError('CSV/TSV fill-series results must remain text cells instead of introducing XLSX numeric types')
    if "if(sourceCells.some(cellNeedsXlsx)&&isDelimited())return ensureXlsxFor('Fill formulas or formatting')" not in SRC:
        raise AssertionError('fill formula/format conversion guard must remain intact')
    print('Spreadsheets CSV/TSV fill-series text preservation contract: OK')
if __name__=='__main__': main()
