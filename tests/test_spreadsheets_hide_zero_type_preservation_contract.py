#!/usr/bin/env python3
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'apps/spreadsheets/view/grid-surface.js'

def main():
    js="""const fs=require('fs'),vm=require('vm');
globalThis.InkDOS2Spreadsheets={};
vm.runInThisContext(fs.readFileSync(%r,'utf8'));
const display=globalThis.InkDOS2Spreadsheets.GridDisplay.display;
function expect(cell,want,label){const got=display(cell);if(got!==want)throw new Error(label+' => '+JSON.stringify(got)+' expected '+JSON.stringify(want))}
expect({v:0,t:'n',style:{hideZero:true}},'', 'numeric zero');
expect({v:'0',t:'s',display:'0',style:{hideZero:true}},'0','text zero');
expect({v:'00',t:'s',display:'00',style:{hideZero:true}},'00','text leading zero');
expect({v:'',t:'n',f:'A1',calculated:0,style:{hideZero:true}},'','numeric formula zero');
expect({v:'',t:'str',f:'A1',calculated:'0',style:{hideZero:true}},'0','text formula zero');
console.log('Spreadsheets hide-zero type-preservation contract: OK');""" % str(SRC)
    subprocess.run(['node','-e',js],check=True,cwd=ROOT)
if __name__=='__main__': main()
