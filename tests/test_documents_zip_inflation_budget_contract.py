#!/usr/bin/env python3
"""Documents: a DOCX entry cannot inflate past its declared size.

A ZIP entry may declare a small uncompressed size (which passes every declared-size budget and the
compression-ratio check) while its deflate stream expands to far more. Reading it must stop as soon
as the output passes the declared size, instead of inflating everything first.
"""
from __future__ import annotations

import json
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECLARED = 1000
ACTUAL = 8 * 1024 * 1024


def build(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr("word/document.xml", b"<w:document/>")
        zf.writestr("bomb.bin", b"\0" * ACTUAL, compress_type=zipfile.ZIP_DEFLATED)
    data = bytearray(path.read_bytes())
    local = data.find(b"PK\x03\x04bomb.bin"[:4])
    while True:
        name_len = struct.unpack_from("<H", data, local + 26)[0]
        if data[local + 30:local + 30 + name_len] == b"bomb.bin":
            break
        local = data.find(b"PK\x03\x04", local + 4)
    struct.pack_into("<L", data, local + 22, DECLARED)
    central = data.find(b"PK\x01\x02")
    while True:
        name_len = struct.unpack_from("<H", data, central + 28)[0]
        if data[central + 46:central + 46 + name_len] == b"bomb.bin":
            break
        central = data.find(b"PK\x01\x02", central + 4)
    struct.pack_into("<L", data, central + 24, DECLARED)
    path.write_bytes(bytes(data))


PROBE = r'''
const fs=require('fs');
const vm=require('vm');
__PRELUDE__
vm.runInThisContext(fs.readFileSync('apps/documents/io/package-reader.js','utf8'),{filename:'package-reader.js'});
(async()=>{
  const pkg=await globalThis.InkDOS2Documents.PackageReader.open(fs.readFileSync(process.argv[2]));
  const ok=new TextDecoder().decode(await pkg.read('word/document.xml'));
  let code='read';
  try{await pkg.read('bomb.bin')}catch(error){code=String(error&&error.code||error)}
  process.stdout.write(JSON.stringify({ok:ok.length>0,code}));
})().catch(error=>{console.error(String(error&&error.code||'error')+': '+String(error&&error.message||error));process.exit(2)});
'''


def run(path: Path, td: Path, prelude: str) -> dict:
    runner = td / "probe.cjs"
    runner.write_text(PROBE.replace("__PRELUDE__", prelude), encoding="utf-8")
    done = subprocess.run(["node", str(runner), str(path)], cwd=ROOT, text=True, capture_output=True, check=False)
    if done.returncode != 0:
        raise AssertionError(f"node exited {done.returncode}: {done.stderr.strip()}")
    return json.loads(done.stdout)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        td = Path(temp)
        package = td / "bomb.zip"
        build(package)
        for label, prelude in (("bundled pako", "vm.runInThisContext(fs.readFileSync('apps/documents/vendor/pako_inflate.min.js','utf8'));"),
                               ("DecompressionStream", "")):
            result = run(package, td, prelude)
            assert result == {"ok": True, "code": "expanded-budget"}, (label, result)
    print("Documents ZIP inflation budget contract: OK")


if __name__ == "__main__":
    main()
