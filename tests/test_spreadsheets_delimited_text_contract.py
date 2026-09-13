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
const enc=new TextEncoder();
function cells(book){
  const sheet=book.sheets[0];
  const out={};
  for(const [ref,cell] of sheet.cells.entries())out[ref]=cell.v;
  return out;
}
const csv='\ufeffid,name,notes\r\n00123,"Doe, Jane","line 1\nline 2"\r\n00007,"He said ""hello""",plain\r\n';
const parsed=codec.parse(enc.encode(csv).buffer,{delimiter:',',fileName:'sample.csv'});
const tsv=codec.parse(enc.encode('code\tlabel\n0009\t"alpha\tbeta"\n').buffer,{delimiter:'\t',fileName:'sample.tsv'});
const round=codec.serialize(parsed.book,{delimiter:',',bom:parsed.bom});
const reparsed=codec.parse(await round.arrayBuffer(),{delimiter:',',fileName:'round.csv'});
const payload={
  csv:cells(parsed.book),
  tsv:cells(tsv.book),
  round:cells(reparsed.book),
  bom:parsed.bom,
  csvSource:parsed.sourceKind,
  tsvSource:tsv.sourceKind,
  mime:round.type,
};
process.stdout.write(JSON.stringify(payload));
'''
    # Wrap in an async IIFE so Blob.arrayBuffer() can be awaited in Node.
    probe = '(async()=>{' + probe + '})().catch(e=>{console.error(e);process.exit(1)})'
    completed = subprocess.run(
        ['node', '-e', probe, str(MODULE)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)

    expected_csv = {
        'A1': 'id', 'B1': 'name', 'C1': 'notes',
        'A2': '00123', 'B2': 'Doe, Jane', 'C2': 'line 1\nline 2',
        'A3': '00007', 'B3': 'He said "hello"', 'C3': 'plain',
    }
    expected_tsv = {
        'A1': 'code', 'B1': 'label',
        'A2': '0009', 'B2': 'alpha\tbeta',
    }
    if result['csv'] != expected_csv:
        raise AssertionError(f'CSV parse mismatch: {result["csv"]!r}')
    if result['tsv'] != expected_tsv:
        raise AssertionError(f'TSV parse mismatch: {result["tsv"]!r}')
    if result['round'] != expected_csv:
        raise AssertionError(f'CSV round-trip mismatch: {result["round"]!r}')
    if result['bom'] is not True:
        raise AssertionError('UTF-8 BOM must be detected and preserved')
    if result['csvSource'] != 'csv' or result['tsvSource'] != 'tsv':
        raise AssertionError(f'Wrong delimited source kinds: {result!r}')
    if result['mime'] != 'text/csv;charset=utf-8':
        raise AssertionError(f'Unexpected CSV MIME type: {result["mime"]!r}')

    print('Spreadsheets CSV/TSV codec contract: OK')


if __name__ == '__main__':
    main()
