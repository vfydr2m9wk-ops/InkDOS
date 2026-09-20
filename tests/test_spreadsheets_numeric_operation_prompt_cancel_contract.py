#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'apps/spreadsheets/ui/chrome-controller.js').read_text(encoding='utf-8')

def main():
    guard="const input=root.prompt(kind==='multiply'?'Multiply selected cells by:':'Divide selected cells by:','2');if(input===null||String(input).trim()==='')return;const f=Number(input);if(Number.isFinite(f))commands.execute('operation.apply',kind,f)"
    if guard not in SRC:
        raise AssertionError('cancelled or blank multiply/divide prompt must not coerce null/empty text to zero and mutate the selection')
    legacy="Number(root.prompt(kind==='multiply'?'Multiply selected cells by:':'Divide selected cells by:','2'))"
    if legacy in SRC:
        raise AssertionError('prompt result must be checked for cancellation/blank input before numeric coercion')
    print('Spreadsheets numeric-operation prompt cancellation contract: OK')
if __name__=='__main__': main()
