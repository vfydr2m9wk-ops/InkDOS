#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'apps/spreadsheets/io/delimited-text.js'


def main() -> None:
    if not MODULE.is_file():
        raise AssertionError('CSV/TSV codec missing: apps/spreadsheets/io/delimited-text.js')

    probe = r'''
const fs=require('fs');
const vm=require('vm');
const path=process.argv[1];
vm.runInThisContext(fs.readFileSync(path,'utf8'),{filename:path});
const codec=globalThis.InkDOS2Spreadsheets?.DelimitedText;
if(!codec)throw new Error('DelimitedText API missing');

function utf16(text,bigEndian){
  const out=new Uint8Array(text.length*2+2);
  if(bigEndian){out[0]=0xFE;out[1]=0xFF}else{out[0]=0xFF;out[1]=0xFE}
  for(let i=0;i<text.length;i++){
    const code=text.charCodeAt(i),offset=2+i*2;
    if(bigEndian){out[offset]=code>>8;out[offset+1]=code&255}
    else{out[offset]=code&255;out[offset+1]=code>>8}
  }
  return out;
}

const text='id,name\r\n00123,Alice\r\n';
async function roundTrip(bytes,fileName){
  const parsed=codec.parse(bytes.buffer,{delimiter:',',fileName});
  const blob=codec.serialize(parsed.book,{delimiter:',',bom:parsed.bom,encoding:parsed.encoding});
  const reparsed=codec.parse(await blob.arrayBuffer(),{delimiter:',',fileName});
  return {
    encoding:parsed.encoding,
    bom:parsed.bom,
    mime:blob.type,
    value:reparsed.book.sheets[0].cells.get('A2')?.v,
    roundEncoding:reparsed.encoding,
    roundBom:reparsed.bom,
  };
}
const le=await roundTrip(utf16(text,false),'utf16le.csv');
const be=await roundTrip(utf16(text,true),'utf16be.csv');
process.stdout.write(JSON.stringify({le,be}));
'''
    probe = '(async()=>{' + probe + '})().catch(e=>{console.error(e);process.exit(1)})'
    completed = subprocess.run(
        ['node', '-e', probe, str(MODULE)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)

    for key, expected_encoding in (('le', 'utf-16le'), ('be', 'utf-16be')):
        item = result[key]
        if item['encoding'] != expected_encoding or item['roundEncoding'] != expected_encoding:
            raise AssertionError(f'{key}: encoding was not preserved: {item!r}')
        if item['bom'] is not True or item['roundBom'] is not True:
            raise AssertionError(f'{key}: BOM was not preserved: {item!r}')
        if item['mime'] != f'text/csv;charset={expected_encoding}':
            raise AssertionError(f'{key}: MIME charset does not match preserved encoding: {item!r}')
        if item['value'] != '00123':
            raise AssertionError(f'{key}: leading-zero string was corrupted: {item!r}')

    print('Spreadsheets CSV UTF-16 encoding/BOM preservation contract: OK')


if __name__ == '__main__':
    main()
