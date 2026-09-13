#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "spreadsheets"
ENGINE = APP / "io" / "delimited-text.js"


def require(text: str, needle: str, message: str) -> None:
    if needle not in text:
        raise SystemExit(message)


def main() -> None:
    if not ENGINE.exists():
        raise SystemExit("Spreadsheets Goal 1 requires io/delimited-text.js for CSV/TSV parsing and serialization")

    opener = (APP / "io" / "file-open-controller.js").read_text(encoding="utf-8")
    saver = (APP / "io" / "save-controller.js").read_text(encoding="utf-8")

    node_script = r'''
const fs = require('fs');
const vm = require('vm');
globalThis.InkDOS2Spreadsheets = {};
vm.runInThisContext(fs.readFileSync(process.argv[1], 'utf8'));
const D = globalThis.InkDOS2Spreadsheets.DelimitedText;
if (!D || typeof D.parse !== 'function' || typeof D.serialize !== 'function') {
  throw new Error('DelimitedText must expose parse() and serialize()');
}

const csv = '\uFEFFid,name,notes,empty\r\n00123,"Doe, Jane","line 1\nline 2",\r\n7,"He said ""hello""",plain,';
const parsed = D.parse(csv, { extension: '.csv' });
const expected = [
  ['id', 'name', 'notes', 'empty'],
  ['00123', 'Doe, Jane', 'line 1\nline 2', ''],
  ['7', 'He said "hello"', 'plain', ''],
];
if (JSON.stringify(parsed.rows) !== JSON.stringify(expected)) {
  throw new Error('CSV parser lost quoted/newline/escaped-quote/empty-field or leading-zero semantics: ' + JSON.stringify(parsed.rows));
}
if (parsed.delimiter !== ',') throw new Error('CSV delimiter metadata was not preserved');
if (parsed.lineEnding !== '\r\n') throw new Error('CSV CRLF metadata was not preserved');
if (parsed.bom !== true) throw new Error('CSV BOM metadata was not preserved');
const csvOut = D.serialize(parsed.rows, parsed);
const csvAgain = D.parse(csvOut, { extension: '.csv' });
if (JSON.stringify(csvAgain.rows) !== JSON.stringify(expected)) throw new Error('CSV semantic round-trip failed');
if (!csvOut.startsWith('\uFEFF')) throw new Error('CSV BOM was not preserved on save');
if (!csvOut.includes('\r\n')) throw new Error('CSV line endings were not preserved on save');

const tsv = 'code\tlabel\n0007\t"alpha\tbeta"\n';
const tsvParsed = D.parse(tsv, { extension: '.tsv' });
if (tsvParsed.delimiter !== '\t') throw new Error('TSV delimiter was not selected from extension');
if (tsvParsed.rows[1][0] !== '0007' || tsvParsed.rows[1][1] !== 'alpha\tbeta') {
  throw new Error('TSV parser corrupted string semantics');
}
const tsvOut = D.serialize(tsvParsed.rows, tsvParsed);
if (tsvOut.includes(',') && !tsvOut.includes('\t')) throw new Error('TSV serializer changed delimiter');
'''
    subprocess.run(["node", "-e", node_script, str(ENGINE)], cwd=ROOT, check=True)

    require(opener, "csv", "Spreadsheets open path must admit CSV")
    require(opener, "tsv", "Spreadsheets open path must admit TSV")
    require(opener, "DelimitedText", "Spreadsheets open path must use the real delimited parser")
    require(saver, "DelimitedText", "Spreadsheets save path must serialize CSV/TSV through the delimited engine")
    require(saver, "Save as XLSX", "Unsupported CSV/TSV workbook features must offer explicit Save as XLSX fallback")

    print("CSV/TSV 2.3 same-format contract passed")


if __name__ == "__main__":
    main()
