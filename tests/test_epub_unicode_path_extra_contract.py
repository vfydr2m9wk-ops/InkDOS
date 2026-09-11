#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unicode_path_extra(raw_name: bytes, unicode_name: str) -> bytes:
    payload = struct.pack("<BI", 1, zlib.crc32(raw_name) & 0xFFFFFFFF) + unicode_name.encode("utf-8")
    return struct.pack("<HH", 0x7075, len(payload)) + payload


def build_unicode_path_epub(path: Path) -> None:
    unicode_chapter = "OEBPS/章节.xhtml"
    entries = [
        (b"mimetype", b"application/epub+zip", b""),
        (
            b"META-INF/container.xml",
            b'''<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>''',
            b"",
        ),
        (
            b"OEBPS/content.opf",
            b'''<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Unicode Path Regression</dc:title></metadata><manifest><item id="c1" href="%E7%AB%A0%E8%8A%82.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>''',
            b"",
        ),
        (
            b"OEBPS/chapter.xhtml",
            b'''<?xml version="1.0" encoding="UTF-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Unicode chapter</h1></body></html>''',
            unicode_path_extra(b"OEBPS/chapter.xhtml", unicode_chapter),
        ),
    ]

    local = bytearray()
    central = bytearray()
    records = []
    for name, payload, extra in entries:
        offset = len(local)
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        local += struct.pack(
            "<IHHHHHIIIHH",
            0x04034B50,
            20,
            0,
            0,
            0,
            0,
            crc,
            len(payload),
            len(payload),
            len(name),
            len(extra),
        )
        local += name + extra + payload
        records.append((name, payload, extra, crc, offset))

    central_offset = len(local)
    for name, payload, extra, crc, offset in records:
        central += struct.pack(
            "<IHHHHHHIIIHHHHHII",
            0x02014B50,
            20,
            20,
            0,
            0,
            0,
            0,
            crc,
            len(payload),
            len(payload),
            len(name),
            len(extra),
            0,
            0,
            0,
            0,
            offset,
        )
        central += name + extra

    eocd = struct.pack(
        "<IHHHHIIH",
        0x06054B50,
        0,
        0,
        len(records),
        len(records),
        len(central),
        central_offset,
        0,
    )
    path.write_bytes(bytes(local + central + eocd))


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        epub = Path(td) / "unicode-path.epub"
        build_unicode_path_epub(epub)
        runner = Path(td) / "probe.cjs"
        runner.write_text(
            r'''
const fs=require('fs');
const vm=require('vm');
vm.runInThisContext(fs.readFileSync('apps/epub/io/package-reader.js','utf8'),{filename:'package-reader.js'});
(async()=>{
  const input=fs.readFileSync(process.argv[2]);
  const pkg=await globalThis.InkDOS2Epub.PackageReader.open(input);
  const path='OEBPS/章节.xhtml';
  const bytes=await pkg.read(path);
  process.stdout.write(JSON.stringify({hasUnicodeChapter:pkg.has(path),chapterText:new TextDecoder().decode(bytes)}));
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
                "EPUB ZIP Unicode Path extra-field names should resolve to packaged entries; "
                f"node exited {completed.returncode}: {completed.stderr.strip()}"
            )
        result = json.loads(completed.stdout)
        assert result["hasUnicodeChapter"] is True, result
        assert "Unicode chapter" in result["chapterText"], result
    print("EPUB Unicode Path extra-field contract: OK")


if __name__ == "__main__":
    main()
