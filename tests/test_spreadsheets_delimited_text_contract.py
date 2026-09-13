#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'apps/spreadsheets/io/delimited-text.js'


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    if not MODULE.is_file():
        raise AssertionError('CSV/TSV codec missing: apps/spreadsheets/io/delimited-text.js')

    file_open = (ROOT / 'apps/spreadsheets/io/file-open-controller.js').read_text(encoding='utf-8')
    workbook_session = (ROOT / 'apps/spreadsheets/engine/workbook-session.js').read_text(encoding='utf-8')
    save_controller = (ROOT / 'apps/spreadsheets/io/save-controller.js').read_text(encoding='utf-8')
    app = (ROOT / 'apps/spreadsheets/app.js').read_text(encoding='utf-8')
    index = (ROOT / 'apps/spreadsheets/index.html').read_text(encoding='utf-8')
    service_worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')

    # Integration contract: CSV/TSV must route into Spreadsheets and preserve
    # their source kind/name rather than being silently promoted to XLSX.
    for marker in ('.csv', '.tsv'):
        require(index, marker, 'Spreadsheets file picker')
    require(index, 'src="io/delimited-text.js"', 'Spreadsheets script graph')
    require(service_worker, '"./apps/spreadsheets/io/delimited-text.js"', 'Spreadsheets offline shell')
    require(file_open, 'NS.DelimitedText.parse', 'Spreadsheets delimited open path')
    require(file_open, "sourceKind==='csv'", 'Spreadsheets CSV source routing')
    require(file_open, "sourceKind==='tsv'", 'Spreadsheets TSV source routing')
    require(workbook_session, "sourceKind==='csv'", 'WorkbookSession CSV naming')
    require(workbook_session, "sourceKind==='tsv'", 'WorkbookSession TSV naming')

    # Same-format save must use the delimited serializer, while the final safety
    # gate prevents XLSX-only state from being silently flattened into text.
    require(save_controller, 'NS.DelimitedText.serialize', 'Delimited same-format save')
    require(save_controller, 'NS.DelimitedText.compatibility', 'Delimited save compatibility gate')
    require(save_controller, "title:'Convert to XLSX?'", 'Delimited save conversion warning')
    require(save_controller, 'session.convertToXlsx()', 'Delimited save explicit XLSX conversion')
    require(save_controller, '{sourceKind:session.sourceKind}', 'Delimited delivery source kind')
    require(app, 'session,dialog,', 'Save controller receives in-app confirmation dialog')

    probe = r'''
const fs=require('fs');
const vm=require('vm');
const path=process.argv[1];
vm.runInThisContext(fs.readFileSync(path,'utf8'),{filename:path});
const codec=globalThis.InkDOS2Spreadsheets?.DelimitedText;
if(!codec)throw new Error('DelimitedText API missing');
if(typeof codec.compatibility!=='function')throw new Error('DelimitedText compatibility() missing');
const enc=new TextEncoder();
function cells(book){
  const sheet=book.sheets[0];
  const out={};
  for(const [ref,cell] of sheet.cells.entries())out[ref]=cell.v;
  return out;
}
const csv='\ufeffid,name,notes,empty\r\n00123,"Doe, Jane","line 1\nline 2",\r\n00007,"He said ""hello""",plain,\r\n';
const parsed=codec.parse(enc.encode(csv).buffer,{delimiter:',',fileName:'sample.csv'});
const tsv=codec.parse(enc.encode('code\tlabel\n0009\t"alpha\tbeta"\n').buffer,{delimiter:'\t',fileName:'sample.tsv'});
const round=codec.serialize(parsed.book,{delimiter:',',bom:parsed.bom,encoding:parsed.encoding});
const reparsed=codec.parse(await round.arrayBuffer(),{delimiter:',',fileName:'round.csv'});
const initiallyCompatible=codec.compatibility(parsed.book);
const cell=parsed.book.sheets[0].cells.get('A2');
cell.f='SUM(A1:A1)';
const formulaCompatibility=codec.compatibility(parsed.book);
cell.f='';
cell.style.font.bold=true;
const styleCompatibility=codec.compatibility(parsed.book);
cell.style.font={};
parsed.book.sheets.push({...parsed.book.sheets[0],name:'Sheet2',cells:new Map()});
const sheetCompatibility=codec.compatibility(parsed.book);
const payload={
  csv:cells(reparsed.book),
  tsv:cells(tsv.book),
  bom:parsed.bom,
  csvSource:parsed.sourceKind,
  tsvSource:tsv.sourceKind,
  mime:round.type,
  cols:reparsed.book.delimitedMeta.cols,
  initiallyCompatible,
  formulaCompatibility,
  styleCompatibility,
  sheetCompatibility,
};
process.stdout.write(JSON.stringify(payload));
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

    expected_csv = {
        'A1': 'id', 'B1': 'name', 'C1': 'notes', 'D1': 'empty',
        'A2': '00123', 'B2': 'Doe, Jane', 'C2': 'line 1\nline 2',
        'A3': '00007', 'B3': 'He said "hello"', 'C3': 'plain',
    }
    expected_tsv = {
        'A1': 'code', 'B1': 'label',
        'A2': '0009', 'B2': 'alpha\tbeta',
    }
    if result['csv'] != expected_csv:
        raise AssertionError(f'CSV semantic round-trip mismatch: {result["csv"]!r}')
    if result['cols'] != 4:
        raise AssertionError(f'Trailing empty CSV column was not preserved: {result["cols"]!r}')
    if result['tsv'] != expected_tsv:
        raise AssertionError(f'TSV parse mismatch: {result["tsv"]!r}')
    if result['bom'] is not True:
        raise AssertionError('UTF-8 BOM must be detected and preserved')
    if result['csvSource'] != 'csv' or result['tsvSource'] != 'tsv':
        raise AssertionError(f'Wrong delimited source kinds: {result!r}')
    if result['mime'] != 'text/csv;charset=utf-8':
        raise AssertionError(f'Unexpected CSV MIME type: {result["mime"]!r}')
    if not result['initiallyCompatible']['compatible']:
        raise AssertionError(f'Plain CSV workbook must remain CSV-compatible: {result["initiallyCompatible"]!r}')
    if result['formulaCompatibility']['compatible'] or 'formulas' not in result['formulaCompatibility']['reasons']:
        raise AssertionError(f'Formula must require XLSX conversion: {result["formulaCompatibility"]!r}')
    if result['styleCompatibility']['compatible'] or 'cell formatting' not in result['styleCompatibility']['reasons']:
        raise AssertionError(f'Formatting must require XLSX conversion: {result["styleCompatibility"]!r}')
    if result['sheetCompatibility']['compatible'] or 'multiple worksheets' not in result['sheetCompatibility']['reasons']:
        raise AssertionError(f'Multiple worksheets must require XLSX conversion: {result["sheetCompatibility"]!r}')

    print('Spreadsheets CSV/TSV codec, routing, save, and compatibility contract: OK')


if __name__ == '__main__':
    main()
