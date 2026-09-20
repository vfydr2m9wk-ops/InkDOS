#!/usr/bin/env python3
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'apps/spreadsheets/engine/formula/evaluator.js'
def main():
    js="""const fs=require('fs'),vm=require('vm');
globalThis.LocalXLSX={encodeRef:(r,c)=>String.fromCharCode(65+c)+(r+1),decodeRef:(ref)=>{const m=/^([A-Z]+)(\\d+)$/.exec(ref);return {r:+m[2]-1,c:m[1].charCodeAt(0)-65}}};
globalThis.InkDOS2SpreadsheetFormulaMath={evaluateArithmetic:(s)=>Function('return ('+s.replace(/%/g,'/100')+')')()};
vm.runInThisContext(fs.readFileSync(SRC,'utf8')); const E=globalThis.InkDOS2Spreadsheets.FormulaEvaluator;
const sheet={name:'Sheet1',cells:new Map([['A1',{v:'00123',t:'s'}],['A2',{v:'FALSE',t:'s'}],['A3',{v:false,t:'b'}],['A4',{v:true,t:'b'}],['A5',{v:0,t:'n'}],['A6',{v:2,t:'n'}]])}; const book={sheets:[sheet]};
function expect(formula,want){const got=E.evaluate(book,sheet,formula);if(got!==want)throw new Error(formula+' => '+got+' expected '+want)}
expect('IF(A1,1,2)','#VALUE!'); expect('IF(A2,1,2)','#VALUE!'); expect('IF(\"text\",1,2)','#VALUE!'); expect('IF(A3,1,2)',2); expect('IF(A4,1,2)',1); expect('IF(A5,1,2)',2); expect('IF(A6,1,2)',1); console.log('Spreadsheets IF condition type-preservation contract: OK');""".replace('SRC',repr(str(SRC)))
    subprocess.run(['node','-e',js],check=True,cwd=ROOT)
if __name__=='__main__': main()
