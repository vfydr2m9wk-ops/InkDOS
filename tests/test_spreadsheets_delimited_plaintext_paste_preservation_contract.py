#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EDITOR=ROOT/'apps/spreadsheets/ui/editor-controller.js'

def main():
    probe=r'''const fs=require('fs'),vm=require('vm');globalThis.InkDOS2Spreadsheets={};vm.runInThisContext(fs.readFileSync(process.argv[1],'utf8'));const f=globalThis.InkDOS2Spreadsheets.assignPlainTextPaste;if(typeof f!=='function')throw new Error('helper missing');function x(v,p){return f({},v,p)}process.stdout.write(JSON.stringify({zero:x('00123',true),decimal:x('12.50',true),date:x('01/02/2026',true),scientific:x('1e3',true),formula:x('=SUM(A1:A2)',true),xlsx:x('00123',false),xlsxFormula:x('=SUM(A1:A2)',false)}));'''
    r=subprocess.run(['node','-e',probe,str(EDITOR)],cwd=ROOT,text=True,capture_output=True,check=True)
    out=json.loads(r.stdout)
    for k,v in [('zero','00123'),('decimal','12.50'),('date','01/02/2026'),('scientific','1e3')]:
        c=out[k]
        if c.get('v')!=v or c.get('t')!='s' or c.get('display')!=v or c.get('f')!='': raise AssertionError((k,c))
    if out['xlsx'].get('v')!=123 or out['xlsx'].get('t')!='n': raise AssertionError(out['xlsx'])
    src=EDITOR.read_text(encoding='utf-8')
    if 'assignPlainTextPaste(cell,value,isDelimited())' not in src: raise AssertionError('paste path is not source-kind aware')
    print('Spreadsheets CSV/TSV plain-text paste preservation contract: OK')
if __name__=='__main__': main()
