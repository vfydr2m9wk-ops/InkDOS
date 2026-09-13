#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITOR = ROOT / 'apps/spreadsheets/engine/workbook-editor.js'


def main() -> None:
    probe = r'''
const fs=require('fs');
const vm=require('vm');
const path=process.argv[1];
globalThis.InkDOS2Spreadsheets={
  FormulaEvaluator:{recalculate(){}},
};
globalThis.LocalXLSX={
  encodeRef(r,c){return String.fromCharCode(65+c)+String(r+1)},
  decodeRef(ref){return{r:Number(ref.slice(1))-1,c:ref.charCodeAt(0)-65}},
};
vm.runInThisContext(fs.readFileSync(path,'utf8'),{filename:path});
const WorkbookEditor=globalThis.InkDOS2Spreadsheets.WorkbookEditor;
if(typeof WorkbookEditor!=='function')throw new Error('WorkbookEditor missing');

function commit(sourceKind,value){
  const sheet={cells:new Map(),merges:[],widths:{},heights:{},maxR:0,maxC:0};
  const session={sourceKind,book:{sheets:[sheet]},activeSheet(){return sheet},markDirty(){}};
  const selection={
    active:{r:0,c:0},range:{r1:0,c1:0,r2:0,c2:0},
    snapshot(){return{active:{...this.active},range:{...this.range}}},
    select(r,c){this.active={r,c};this.range={r1:r,c1:c,r2:r,c2:c}},
    restore(){}
  };
  const history={push(){},undo(){},redo(){}};
  const editor=new WorkbookEditor({session,selection,history,onChange(){}});
  editor.commitValue(value,0,0);
  return sheet.cells.get('A1');
}
const payload={
  csvLeadingZero:commit('csv','00123'),
  tsvLeadingZero:commit('tsv','0009'),
  csvDecimalText:commit('csv','12.50'),
  xlsxNumber:commit('xlsx','00123'),
};
process.stdout.write(JSON.stringify(payload));
'''
    completed = subprocess.run(
        ['node', '-e', probe, str(EDITOR)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)

    for key, expected in (
        ('csvLeadingZero', '00123'),
        ('tsvLeadingZero', '0009'),
        ('csvDecimalText', '12.50'),
    ):
        cell = result[key]
        if cell.get('v') != expected or cell.get('t') != 's' or cell.get('display') != expected:
            raise AssertionError(f'{key} must remain exact text in delimited sessions: {cell!r}')

    xlsx = result['xlsxNumber']
    if xlsx.get('v') != 123 or xlsx.get('t') != 'n':
        raise AssertionError(f'XLSX numeric inference must remain unchanged: {xlsx!r}')

    print('Spreadsheets CSV/TSV direct-edit text preservation contract: OK')


if __name__ == '__main__':
    main()
