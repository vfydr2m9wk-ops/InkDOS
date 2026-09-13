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

    for marker in ('.csv', '.tsv'):
        require(index, marker, 'Spreadsheets file picker')
    require(index, 'src="io/delimited-text.js"', 'Spreadsheets script graph')
    require(service_worker, '"./apps/spreadsheets/io/delimited-text.js"', 'Spreadsheets offline shell')
    require(file_open, 'NS.DelimitedText.parse', 'Spreadsheets delimited open path')
    require(file_open, "sourceKind==='csv'", 'Spreadsheets CSV source routing')
    require(file_open, "sourceKind==='tsv'", 'Spreadsheets TSV source routing')
    require(workbook_session, "sourceKind==='csv'", 'WorkbookSession CSV naming')
    require(workbook_session, "sourceKind==='tsv'", 'WorkbookSession TSV naming')

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
if(typeof codec.detectDelimiter!=='function')throw new Error('DelimitedText detectDelimiter() missing');
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
const semi='Username; Identifier;First name;Last name\nuser01;1001;Alex;Morgan\nuser02;0007;Taylor;Lee\n';
const semiParsed=codec.parse(enc.encode(semi).buffer,{fileName:'sample.csv'});
const semiQuoted='id;name;note\n1;"Doe, Jane";"comma, stays quoted"\n';
const semiQuotedParsed=codec.parse(enc.encode(semiQuoted).buffer,{fileName:'quoted-semicolon.csv'});
const commaQuoted='id,name,note\n1,"alpha;beta","semicolon; stays quoted"\n';
const commaQuotedParsed=codec.parse(enc.encode(commaQuoted).buffer,{fileName:'quoted-comma.csv'});
const oneColumn=codec.parse(enc.encode('single\nvalue\n').buffer,{fileName:'one.csv'});
const semiRound=codec.serialize(semiParsed.book);
const semiRoundText=await semiRound.text();
const semiReparsed=codec.parse(await semiRound.arrayBuffer(),{fileName:'round-semi.csv'});
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
  semicolon:cells(semiParsed.book),
  semicolonDelimiter:semiParsed.book.delimitedMeta.delimiter,
  semicolonLineEnding:semiParsed.book.delimitedMeta.lineEnding,
  semicolonFinalSeparator:semiParsed.book.delimitedMeta.finalRecordSeparator,
  semicolonRoundText:semiRoundText,
  semicolonRoundDelimiter:semiReparsed.book.delimitedMeta.delimiter,
  semiQuotedDelimiter:semiQuotedParsed.book.delimitedMeta.delimiter,
  commaQuotedDelimiter:commaQuotedParsed.book.delimitedMeta.delimiter,
  oneColumnDelimiter:oneColumn.book.delimitedMeta.delimiter,
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
    expected_semicolon = {
        'A1': 'Username', 'B1': ' Identifier', 'C1': 'First name', 'D1': 'Last name',
        'A2': 'user01', 'B2': '1001', 'C2': 'Alex', 'D2': 'Morgan',
        'A3': 'user02', 'B3': '0007', 'C3': 'Taylor', 'D3': 'Lee',
    }
    if result['csv'] != expected_csv:
        raise AssertionError(f'CSV semantic round-trip mismatch: {result["csv"]!r}')
    if result['cols'] != 4:
        raise AssertionError(f'Trailing empty CSV column was not preserved: {result["cols"]!r}')
    if result['tsv'] != expected_tsv:
        raise AssertionError(f'TSV parse mismatch: {result["tsv"]!r}')
    if result['semicolon'] != expected_semicolon:
        raise AssertionError(f'Semicolon CSV detection mismatch: {result["semicolon"]!r}')
    if result['semicolonDelimiter'] != ';':
        raise AssertionError(f'Semicolon CSV delimiter was not retained: {result["semicolonDelimiter"]!r}')
    if result['semiQuotedDelimiter'] != ';':
        raise AssertionError(f'Quoted commas confused semicolon detection: {result["semiQuotedDelimiter"]!r}')
    if result['commaQuotedDelimiter'] != ',':
        raise AssertionError(f'Quoted semicolons confused comma detection: {result["commaQuotedDelimiter"]!r}')
    if result['oneColumnDelimiter'] != ',':
        raise AssertionError(f'One-column CSV did not fall back to comma: {result["oneColumnDelimiter"]!r}')
    if result['semicolonLineEnding'] != '\n':
        raise AssertionError(f'LF source line ending was not retained: {result["semicolonLineEnding"]!r}')
    if result['semicolonFinalSeparator'] is not True:
        raise AssertionError('Final CSV record separator was not retained')
    if result['semicolonRoundText'] != 'Username; Identifier;First name;Last name\nuser01;1001;Alex;Morgan\nuser02;0007;Taylor;Lee\n':
        raise AssertionError(f'Semicolon/LF same-format serialization changed source convention: {result["semicolonRoundText"]!r}')
    if result['semicolonRoundDelimiter'] != ';':
        raise AssertionError(f'Reopened semicolon CSV changed delimiter: {result["semicolonRoundDelimiter"]!r}')
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
