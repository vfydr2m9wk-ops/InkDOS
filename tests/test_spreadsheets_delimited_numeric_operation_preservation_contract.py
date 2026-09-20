#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'apps/spreadsheets/engine/workbook-editor.js').read_text(encoding='utf-8')

def main():
    allowed="const allowed=['sum','average','min','max','count','multiply','divide','percent'];if(!allowed.includes(kind))return false"
    if allowed not in SRC:
        raise AssertionError('numeric operation engine must reject unknown operation kinds before mutation')
    guard="delimited=this.session.sourceKind==='csv'||this.session.sourceKind==='tsv',requiresXlsx=['sum','average','min','max','count'].includes(kind)||kind==='percent';if(delimited&&requiresXlsx)return false"
    if guard not in SRC:
        raise AssertionError('direct engine formula/percentage operations must fail closed in CSV/TSV')
    needle="if(this.session.sourceKind==='csv'||this.session.sourceKind==='tsv'){cell.v=String(cell.v);cell.t='s'}"
    if needle not in SRC:
        raise AssertionError('CSV/TSV multiply/divide results must remain exact string cells')
    zero_guard="if(!Number.isFinite(f)||(kind==='divide'&&f===0))return false"
    if zero_guard not in SRC:
        raise AssertionError('multiply-by-zero must remain valid while divide-by-zero fails closed')
    blank_guard="const cell=this.sheet().cells.get(k);if(!cell)continue;const raw=cell.calculated??cell.v;if(raw==null||typeof raw==='boolean'||cell.t==='b'||(!delimited&&cell.t==='s')||String(raw).trim()==='')continue"
    if blank_guard not in SRC:
        raise AssertionError('numeric operations must preserve missing/blank cells instead of coercing them to zero')
    boolean_guard="if(raw==null||typeof raw==='boolean'||cell.t==='b'||(!delimited&&cell.t==='s')||String(raw).trim()==='')continue"
    if boolean_guard not in SRC:
        raise AssertionError('numeric operations must preserve boolean cells instead of coercing true/false into numbers')
    finite_result="if(!Number.isFinite(result))continue;cell.v=result"
    if finite_result not in SRC:
        raise AssertionError('numeric operations must not persist non-finite overflow results')
    if "kind==='percent'?'Percentage formatting'" not in (ROOT/'apps/spreadsheets/ui/editor-controller.js').read_text(encoding='utf-8'):
        raise AssertionError('percentage formatting must remain behind explicit XLSX conversion')
    print('Spreadsheets CSV/TSV numeric-operation text preservation contract: OK')
if __name__=='__main__': main()
