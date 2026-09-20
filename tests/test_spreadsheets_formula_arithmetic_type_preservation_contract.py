#!/usr/bin/env python3
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'apps/spreadsheets/engine/formula/evaluator.js'

def main():
    js=f'''const fs=require('fs'),vm=require('vm');
globalThis.LocalXLSX={{encodeRef:(r,c)=>String.fromCharCode(65+c)+(r+1),decodeRef:(ref)=>{{const m=/^([A-Z]+)(\\d+)$/.exec(ref);return {{r:+m[2]-1,c:m[1].charCodeAt(0)-65}}}}}};
globalThis.InkDOS2SpreadsheetFormulaMath={{evaluateArithmetic:(s)=>Function('return ('+s.replace(/%/g,'/100')+')')()}};
vm.runInThisContext(fs.readFileSync({str(SRC)!r},'utf8'));
const E=globalThis.InkDOS2Spreadsheets.FormulaEvaluator;
const sheet={{name:'Sheet1',cells:new Map([['A1',{{v:'00123',t:'s'}}],['A2',{{v:true,t:'b'}}],['A3',{{v:7,t:'n'}}],['A4',{{v:2,t:'n'}}]] )}}; const book={{sheets:[sheet]}};
function expect(formula,want){{const got=E.evaluate(book,sheet,formula);if(got!==want)throw new Error(formula+' => '+got+' expected '+want)}}
expect('A1+1','#VALUE!'); expect('A2+1','#VALUE!'); expect('A3+A4',9); expect('A3*2',14);
sheet.cells.set('A5',{{v:'',t:'n',f:'A3+A4'}}); expect('A5+1',10);
console.log('Spreadsheets formula arithmetic reference type-preservation contract: OK');'''
    subprocess.run(['node','-e',js],check=True,cwd=ROOT)
if __name__=='__main__': main()
