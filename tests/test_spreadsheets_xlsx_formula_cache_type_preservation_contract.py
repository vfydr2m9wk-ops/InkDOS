#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'apps/spreadsheets/io/xlsx-engine.js'

def main():
    source=SRC.read_text(encoding='utf-8')
    required=[
        "if(typeof cached==='boolean'){node.setAttribute('t','b');v.textContent=cached?'1':'0'}",
        "else if(typeof cached==='string'&&/^#(?:NULL!|DIV\\/0!|VALUE!|REF!|NAME\\?|NUM!|N\\/A|SPILL!|CALC!)$/.test(cached)){node.setAttribute('t','e');v.textContent=cached}",
        "else if(typeof cached==='string'){node.setAttribute('t','str');v.textContent=cached}",
        "else if(typeof cached==='number'&&Number.isFinite(cached))v.textContent=String(cached)",
    ]
    for guard in required:
        if guard not in source:
            raise AssertionError('XLSX formula cached-result type preservation guard missing: '+guard)
    forbidden=[
        "cached!==''&&cached!=null&&Number.isFinite(Number(cached))",
        "else if(Number.isFinite(Number(cached)))v.textContent=String(cached)",
    ]
    for legacy in forbidden:
        if legacy in source:
            raise AssertionError('legacy formula cache numeric coercion remains: '+legacy)
    print('Spreadsheets XLSX formula cached-result type preservation contract: OK')
if __name__=='__main__': main()
