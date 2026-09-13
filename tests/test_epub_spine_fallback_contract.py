#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'apps/epub/engine/book-model.js').read_text(encoding='utf-8')


def require(needle: str, label: str) -> None:
    if needle not in SOURCE:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    # EPUB permits a foreign resource in the spine when its manifest item provides
    # a fallback chain to an EPUB content document. EPUB content documents include
    # XHTML and SVG, so the resolver must accept either as the terminal readable item.
    require("fallback=attr(item,'fallback')", 'Manifest fallback metadata')
    require('fallback,properties', 'Manifest item fallback retention')
    require('function resolveSpineItem(item)', 'Spine fallback resolver')
    require("const EPUB_CONTENT_TYPES=new Set(['application/xhtml+xml','image/svg+xml'])", 'EPUB content document media types')
    require('EPUB_CONTENT_TYPES.has(candidate.mediaType)', 'Readable EPUB content fallback acceptance')
    require("fail('spine-fallback'", 'Broken/cyclic fallback rejection')
    require('const resolved=resolveSpineItem(item)', 'Spine uses resolved fallback')


if __name__ == '__main__':
    main()
