#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_cp437_epub(path: Path) -> None:
    entries = [
        (b"mimetype", b"application/epub+zip"),
        (b"META-INF/container.xml", b'''<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'''),
        (b"OEBPS/content.opf", b'''<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>CP437 Regression</dc:title></metadata><manifest><item id="c1" href="caf\xc3\xa9.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>'''),
        (b"OEBPS/caf\x82.xhtml", b'''<?xml version="1.0" encoding="UTF-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>CP437 chapter</h1></body></html>'''),
    ]
    local = bytearray()
    central = bytearray()
    records = []
    for name, payload in entries:
        offset = len(local)
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        local += struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0, 0, 0, 0, crc, len(payload), len(payload), len(name), 0)
        local += name + payload
        records.append((name, payload, crc, offset))
    central_offset = len(local)
    for name, payload, crc, offset in records:
        central += struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, 0, 0, 0, 0, crc, len(payload), len(payload), len(name), 0, 0, 0, 0, 0, offset)
        central += name
    eocd = struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(records), len(records), len(central), central_offset, 0)
    path.write_bytes(bytes(local + central + eocd))


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        epub = Path(td) / "cp437.epub"
        build_cp437_epub(epub)
        runner = Path(td) / "probe.cjs"
        runner.write_text(
            r'''
const fs=require('fs');
const vm=require('vm');
vm.runInThisContext(fs.readFileSync('apps/epub/io/package-reader.js','utf8'),{filename:'package-reader.js'});
(async()=>{
  const input=fs.readFileSync(process.argv[2]);
  const pkg=await globalThis.InkDOS2Epub.PackageReader.open(input);
  process.stdout.write(JSON.stringify({entryCount:pkg.entryCount,hasUnicodeChapter:pkg.has('OEBPS/café.xhtml')}));
})().catch(error=>{console.error(String(error&&error.code||'error')+': '+String(error&&error.message||error));process.exit(2)});
''',
            encoding="utf-8",
        )
        completed = subprocess.run(
            ["node", str(runner), str(epub)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "EPUB with a standards-compatible legacy ZIP filename should open; "
                f"node exited {completed.returncode}: {completed.stderr.strip()}"
            )
        result = json.loads(completed.stdout)
        assert result == {"entryCount": 4, "hasUnicodeChapter": True}, result
    print("EPUB legacy ZIP filename encoding contract: OK")


if __name__ == "__main__":
    main()
