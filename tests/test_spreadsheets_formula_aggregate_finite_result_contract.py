#!/usr/bin/env python3
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'apps/spreadsheets/engine/formula/evaluator.js'

def main():
    js=f'''const fs=require('fs'),vm=require('vm');
globalThis.LocalXLSX={{encodeRef:(r,c)=>String.fromCharCode(65+c)+(r+1),decodeRef:(ref)=>{{const m=/^([A-Z]+)(\\d+)$/.exec(ref);return {{r:+m[2]-1,c:m[1].charCodeAt(0)-65}}}}}};
globalThis.InkDOS2SpreadsheetFormulaMath={{evaluateArithmetic:()=>0}};
vm.runInThisContext(fs.readFileSync({str(SRC)!r},'utf8'));
const E=globalThis.InkDOS2Spreadsheets.FormulaEvaluator;
const sheet={{name:'Sheet1',cells:new Map()}}; const book={{sheets:[sheet]}};
function expect(formula,want){{const got=E.evaluate(book,sheet,formula);if(got!==want)throw new Error(formula+' => '+got+' expected '+want)}}
expect('SUM(1e308,1e308)','#NUM!');
expect('PRODUCT(1e308,2)','#NUM!');
expect('AVERAGE(1e308,1e308)','#NUM!');
expect('SUM(2,3)',5); expect('PRODUCT(2,3)',6); expect('AVERAGE(2,4)',3);
sheet.cells.set('A1',{{v:'00123',t:'s'}}); sheet.cells.set('A2',{{v:true,t:'b'}}); sheet.cells.set('A3',{{v:7,t:'n'}});
expect('SUM(A1:A3)',7); expect('COUNT(A1:A3)',1); expect('AVERAGE(A1:A3)',7);
expect('SUM(A1)',0); expect('COUNT(A2)',0); expect('SUM("2",3)',5);
console.log('Spreadsheets formula aggregate finite-result contract: OK');'''
    subprocess.run(['node','-e',js],check=True,cwd=ROOT)
if __name__=='__main__': main()
