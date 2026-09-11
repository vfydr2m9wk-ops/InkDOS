#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'apps/epub/engine/book-model.js').read_text(encoding='utf-8')


def require(needle: str, label: str) -> None:
    if needle not in SOURCE:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    # EPUB permits a foreign resource in the spine when its manifest item provides
    # a fallback chain to an EPUB content document. The reader must resolve the
    # fallback instead of silently dropping every non-XHTML spine item.
    require("const fallback=attr(item,'fallback')", 'Manifest fallback metadata')
    require('fallback,properties', 'Manifest item fallback retention')
    require('function resolveSpineItem(item)', 'Spine fallback resolver')
    require("candidate.mediaType==='application/xhtml+xml'", 'Readable XHTML fallback acceptance')
    require("fail('spine-fallback'", 'Broken/cyclic fallback rejection')
    require('const resolved=resolveSpineItem(item)', 'Spine uses resolved fallback')


if __name__ == '__main__':
    main()
