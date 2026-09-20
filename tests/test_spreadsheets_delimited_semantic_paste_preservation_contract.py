#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'apps/spreadsheets/ui/editor-controller.js').read_text(encoding='utf-8')

def main():
    needle="if(isDelimited()&&!cellNeedsXlsx(cell)){const text=String(cell.v??'');cell.v=text;cell.t='s';cell.f='';cell.display=text}"
    if needle not in SRC:
        raise AssertionError('semantic paste into CSV/TSV must normalize ordinary cells to exact text')
    if "if(payloadNeedsXlsx(payload)&&isDelimited())return ensureXlsxFor('Paste formulas or formatting')" not in SRC:
        raise AssertionError('formula/format conversion guard must remain intact')
    print('Spreadsheets CSV/TSV semantic-paste text preservation contract: OK')
if __name__=='__main__': main()
