#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    index = read('apps/epub/index.html')
    package_reader = read('apps/epub/io/package-reader.js')
    service_worker = read('service-worker.js')
    vendor = ROOT / 'apps/epub/vendor/pako_inflate.min.js'

    if not vendor.is_file():
        raise AssertionError('EPUB WebKit deflate fallback: bundled pako inflater is missing')

    pako_script = 'src="vendor/pako_inflate.min.js"'
    reader_script = 'src="io/package-reader.js"'
    require(index, pako_script, 'EPUB WebKit deflate fallback')
    require(index, reader_script, 'EPUB WebKit deflate fallback')
    if index.index(pako_script) > index.index(reader_script):
        raise AssertionError('EPUB WebKit deflate fallback: pako must load before package-reader')

    require(package_reader, "global.pako&&typeof global.pako.inflateRaw==='function'", 'EPUB WebKit deflate fallback')
    require(package_reader, 'global.pako.inflateRaw(bytes)', 'EPUB WebKit deflate fallback')
    require(package_reader, "fail('deflate-failed'", 'EPUB WebKit deflate fallback')
    require(service_worker, '"./apps/epub/vendor/pako_inflate.min.js"', 'EPUB offline inflater')

    print('EPUB WebKit deflate fallback contract: OK')


if __name__ == '__main__':
    main()
