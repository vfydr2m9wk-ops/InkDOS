#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_minimal_epub(path: Path) -> None:
    container = b'''<?xml version="1.0" encoding="UTF-8"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'''
    opf = b'''<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>ZIP64 Regression</dc:title></metadata><manifest><item id="c1" href="c1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>'''
    chapter = b'''<?xml version="1.0" encoding="UTF-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>ZIP64 chapter</h1><p>InkDOS regression.</p></body></html>'''
    with zipfile.ZipFile(path, "w", allowZip64=True) as zf:
        zf.writestr("mimetype", b"application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_STORED)
        zf.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_STORED)
        zf.writestr("OEBPS/c1.xhtml", chapter, compress_type=zipfile.ZIP_STORED)


def promote_to_zip64_eocd(path: Path) -> None:
    data = bytearray(path.read_bytes())
    eocd = data.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise AssertionError("fixture EOCD missing")
    (
        signature,
        disk,
        central_disk,
        disk_count,
        total_count,
        central_size,
        central_offset,
        comment_len,
    ) = struct.unpack_from("<4s4H2LH", data, eocd)
    if signature != b"PK\x05\x06" or comment_len != 0 or disk != 0 or central_disk != 0:
        raise AssertionError("unexpected base ZIP layout")

    zip64_eocd = struct.pack(
        "<4sQ2H2L4Q",
        b"PK\x06\x06",
        44,
        45,
        45,
        0,
        0,
        disk_count,
        total_count,
        central_size,
        central_offset,
    )
    zip64_locator = struct.pack("<4sLQL", b"PK\x06\x07", 0, eocd, 1)
    legacy_eocd = struct.pack(
        "<4s4H2LH",
        b"PK\x05\x06",
        0,
        0,
        0xFFFF,
        0xFFFF,
        0xFFFFFFFF,
        0xFFFFFFFF,
        0,
    )
    path.write_bytes(data[:eocd] + zip64_eocd + zip64_locator + legacy_eocd)


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        epub = Path(td) / "zip64.epub"
        build_minimal_epub(epub)
        promote_to_zip64_eocd(epub)
        runner = Path(td) / "probe.cjs"
        runner.write_text(
            r'''
const fs=require('fs');
const vm=require('vm');
vm.runInThisContext(fs.readFileSync('apps/epub/io/package-reader.js','utf8'),{filename:'package-reader.js'});
(async()=>{
  const input=fs.readFileSync(process.argv[2]);
  const pkg=await globalThis.InkDOS2Epub.PackageReader.open(input);
  const mime=new TextDecoder().decode(await pkg.read('mimetype'));
  process.stdout.write(JSON.stringify({entryCount:pkg.entryCount,mime,hasChapter:pkg.has('OEBPS/c1.xhtml')}));
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
                "EPUB ZIP64 container should open successfully; "
                f"node exited {completed.returncode}: {completed.stderr.strip()}"
            )
        result = json.loads(completed.stdout)
        assert result == {
            "entryCount": 4,
            "mime": "application/epub+zip",
            "hasChapter": True,
        }, result
    print("EPUB ZIP64 compatibility contract: OK")


if __name__ == "__main__":
    main()
