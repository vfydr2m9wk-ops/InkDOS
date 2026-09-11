#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'apps/epub/engine/book-model.js').read_text(encoding='utf-8')


def require(needle: str) -> None:
    if needle not in SOURCE:
        raise AssertionError(f'EPUB XML encoding contract: missing {needle!r}')


def main() -> None:
    # EPUB 3 XML resources may be UTF-8 or UTF-16. The reader must detect
    # BOM/signature before DOMParser instead of forcing every XML resource
    # through a fatal UTF-8 TextDecoder.
    require('function decodeXmlText(bytes,label)')
    require("new TextDecoder('utf-16le',{fatal:true})")
    require("new TextDecoder('utf-16be',{fatal:true})")
    require("bytes[0]===0xff&&bytes[1]===0xfe")
    require("bytes[0]===0xfe&&bytes[1]===0xff")
    require("bytes[0]===0x3c&&bytes[1]===0x00")
    require("bytes[0]===0x00&&bytes[1]===0x3c")
    require('const text=decodeXmlText(bytes,label)')
    require('NS.BookModel={build,parseXml,decodeXmlText,resolve}')
    print('EPUB XML encoding contract: OK')


if __name__ == '__main__':
    main()
