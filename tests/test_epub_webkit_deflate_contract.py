#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    package_reader = read('apps/epub/io/package-reader.js')
    service_worker = read('service-worker.js')
    vendor = ROOT / 'apps/epub/vendor/pako_inflate.min.js'

    if not vendor.is_file():
        raise AssertionError('EPUB WebKit deflate fallback: app-local inflater is missing')

    # EPUB must not depend exclusively on DecompressionStream('deflate-raw'):
    # some WKWebView/WebKit hosts do not expose a compatible raw-DEFLATE stream.
    require(package_reader, "vendor/pako_inflate.min.js", 'EPUB WebKit deflate fallback')
    if '../documents/' in package_reader or '../spreadsheets/' in package_reader:
        raise AssertionError('EPUB WebKit deflate fallback: cross-app dependency is forbidden')
    require(package_reader, "global.pako&&typeof global.pako.inflateRaw==='function'", 'EPUB WebKit deflate fallback')
    require(package_reader, 'global.pako.inflateRaw(bytes)', 'EPUB WebKit deflate fallback')
    require(package_reader, "script.addEventListener('load'", 'EPUB WebKit deflate fallback')
    require(package_reader, "fail('deflate-failed'", 'EPUB WebKit deflate fallback')
    require(service_worker, '"./apps/epub/vendor/pako_inflate.min.js"', 'EPUB offline inflater')

    print('EPUB WebKit deflate fallback contract: OK')


if __name__ == '__main__':
    main()
