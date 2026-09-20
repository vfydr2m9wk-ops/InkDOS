#!/usr/bin/env python3
from pathlib import Path
import subprocess, textwrap
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'apps/spreadsheets/engine/workbook-editor.js'

def main():
    source=SRC.read_text(encoding='utf-8')
    guard="if(raw==null||typeof raw==='boolean'||cell.t==='b'||(!delimited&&cell.t==='s')||String(raw).trim()==='')continue"
    if guard not in source:
        raise AssertionError('XLSX numeric operations must not coerce explicit text cells into numbers')
    js=textwrap.dedent(f'''\
      globalThis.LocalXLSX={{
        encodeRef:(r,c)=>String.fromCharCode(65+c)+(r+1),
        decodeRef:(ref)=>({{r:Number(ref.slice(1))-1,c:ref.charCodeAt(0)-65}}),
        decodeRange:()=>({{r1:0,c1:0,r2:0,c2:0}})
      }};
      globalThis.InkDOS2Spreadsheets={{FormulaEvaluator:{{recalculate:()=>{{}}}}}};
      require({str(SRC)!r});
      const cells=new Map([
        ['A1',{{v:'00123',f:'',t:'s',display:'00123',style:{{}}}}],
        ['B1',{{v:10,f:'',t:'n',display:'10',style:{{}}}}],
        ['C1',{{v:true,f:'',t:'b',display:'TRUE',style:{{}}}}]
      ]);
      const sheet={{cells,merges:[],widths:{{}},heights:{{}},maxR:0,maxC:2}};
      const selection={{active:{{r:0,c:0}},range:{{r1:0,c1:0,r2:0,c2:2}},snapshot:()=>({{}}),select:()=>{{}}}};
      const session={{sourceKind:'xlsx',book:{{sheets:[sheet]}},activeSheet:()=>sheet,markDirty:()=>{{}}}};
      const history={{push:()=>{{}},undo:()=>false,redo:()=>false}};
      const editor=new globalThis.InkDOS2Spreadsheets.WorkbookEditor({{session,selection,history}});
      if(!editor.operation('multiply',2)) throw new Error('multiply should execute');
      if(cells.get('A1').v!=='00123'||cells.get('A1').t!=='s') throw new Error('explicit XLSX text was coerced');
      if(cells.get('B1').v!==20||cells.get('B1').t!=='n') throw new Error('numeric XLSX cell did not mutate');
      if(cells.get('C1').v!==true||cells.get('C1').t!=='b') throw new Error('boolean XLSX cell was coerced');
      if(!editor.operation('percent')) throw new Error('percent should execute for XLSX');
      if(cells.get('A1').v!=='00123'||cells.get('A1').t!=='s') throw new Error('percent coerced explicit XLSX text');
      if(cells.get('B1').v!==0.2) throw new Error('percent did not mutate numeric XLSX cell');
    ''')
    proc=subprocess.run(['node','-e',js],cwd=ROOT,text=True,capture_output=True)
    if proc.returncode:
        raise AssertionError('runtime XLSX numeric-text preservation failed: '+(proc.stderr or proc.stdout))
    print('Spreadsheets XLSX numeric-text operation preservation contract: OK')
if __name__=='__main__': main()
