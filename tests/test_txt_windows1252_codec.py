#!/usr/bin/env python3
"""Plain Text: a file that is not valid UTF-8 opens as Windows-1252 and saves back to the same bytes."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = r"""
require('./apps/txt/txt-codec.js');require('./apps/txt/export-verify.js');
const C=globalThis.InkDOS2.TxtCodec,V=globalThis.InkDOS2.TxtExportVerify,assert=require('assert');
// Synthetic Windows-1252 text with CRLF, accents, byte 0x80 (the euro sign in browsers; Node's decoder differs, so only the round trip is checked) and the five undefined bytes (0x81 0x8D 0x8F 0x90 0x9D)
const bytes=Uint8Array.from([0x41,0xe7,0xe3,0x6f,0x20,0x80,0x0d,0x0a,0x81,0x8d,0x8f,0x90,0x9d,0xff]);
const d=C.decode(bytes);assert.strictEqual(d.encoding,'windows-1252');assert.strictEqual(d.text.slice(0,5),'A\u00e7\u00e3o ');
const le=C.detectLineEnding(d.text),out=C.encode(C.normalize(d.text),{encoding:d.encoding,bom:d.bom,lineEnding:le});
assert.deepStrictEqual(Array.from(out),Array.from(bytes));
V.verify(out,{text:C.normalize(d.text),encoding:d.encoding,bom:d.bom,lineEnding:le});
assert.throws(()=>C.encode('\u{1F600}',{encoding:'windows-1252'}),/cannot be saved in Windows-1252/);
// Valid UTF-8 is unchanged
assert.strictEqual(C.decode(new TextEncoder().encode('Ação')).encoding,'utf-8');
console.log('Plain Text Windows-1252 codec: OK');
"""


def main():
    subprocess.run(['node', '-e', SCRIPT], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
