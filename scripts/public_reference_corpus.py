#!/usr/bin/env python3
"""Harvest Office files that were published on the web next to a PDF made by Office itself.

Common Crawl indexes billions of captured URLs. This tool scans its columnar index (Parquet on
data.commoncrawl.org, read remotely with DuckDB - only a few small columns travel) for .ppt/.pptx,
.doc/.docx and .xls/.xlsx captures that have a .pdf capture with the same file name on the same
site (/lecture3.pptx + /lecture3.pdf, or /1/talk.pptx + /2/talk.pdf in repositories). Both are fetched straight from the crawl archives
with HTTP range requests, and a pair is kept only when the PDF says it was produced by the
matching Office application (PowerPoint, Word or Excel), neither capture was truncated, and the
Office file rendered by LibreOffice has a compatible page count and shares >= 70% of its words
with the PDF (name-matched files can be different documents).

The result is a corpus with real Office references for scripts/presentations_acceptance.py,
scripts/presentations_fidelity.py and the other acceptance tools ("deck.pptx" + "deck.pdf").
Files are public web documents; they go to --out, never into the repository.

    python3 scripts/public_reference_corpus.py --kind presentations --out /tmp/ref-corpus --pairs 80
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

DATA = 'https://data.commoncrawl.org/'
CRAWLS = ('CC-MAIN-2024-33', 'CC-MAIN-2024-18', 'CC-MAIN-2023-50', 'CC-MAIN-2023-23', 'CC-MAIN-2022-49')
KINDS = {
    'presentations': {'mimes': {'application/vnd.ms-powerpoint': '.ppt',
                                'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx'},
                      'producer': re.compile(r'PowerPoint', re.I)},
    'documents': {'mimes': {'application/msword': '.doc',
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'},
                  'producer': re.compile(r'Microsoft.{0,4}Word|Word for', re.I)},
    'spreadsheets': {'mimes': {'application/vnd.ms-excel': '.xls',
                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx'},
                     'producer': re.compile(r'Excel', re.I)},
}
PDF = 'application/pdf'
UA = {'User-Agent': 'InkDOS-reference-corpus/1 (+fidelity testing)'}


def fetch(url: str, headers: dict | None = None, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def index_parts(crawl: str) -> list[str]:
    paths = gzip.decompress(fetch(f'{DATA}crawl-data/{crawl}/cc-index-table.paths.gz')).decode().split()
    return [p for p in paths if '/subset=warc/' in p]


def stem_of(url: str) -> str | None:
    """Pairing key: site + file name without extension, normalised (repositories often keep the PDF
    in another folder of the same site: /1/talk.pptx and /2/talk.pdf)."""
    from urllib.parse import unquote, urlsplit
    parts = urlsplit(url.split('#')[0])
    m = re.match(r'^(.*?)\.(pptx?|docx?|xlsx?|pdf)$', unquote(parts.path.rsplit('/', 1)[-1]), re.I)
    if not m or parts.query:
        return None
    name = re.sub(r'[\W_]+', '', re.sub(r'\(\d+\)$', '', m.group(1).strip()).lower())
    host = parts.netloc.lower().removeprefix('www.')
    return f'{host}/{name}' if len(name) >= 4 else None


def candidates(con, part: str, kind: dict) -> list[tuple[dict, dict]]:
    mimes = list(kind['mimes']) + [PDF]
    rows = con.execute(
        f"select url, content_mime_detected, warc_filename, warc_record_offset, warc_record_length "
        f"from read_parquet('{DATA}{part}') where content_mime_detected in ({','.join('?' * len(mimes))}) "
        f"and fetch_status = 200 and (content_truncated is null or content_truncated = '')", mimes).fetchall()
    office, pdfs = {}, {}
    for url, mime, wf, off, length in rows:
        st = stem_of(url)
        if not st:
            continue
        rec = {'url': url, 'mime': mime, 'warc': wf, 'offset': off, 'length': length}
        (pdfs if mime == PDF else office).setdefault(st, rec)
    return [(office[s], pdfs[s]) for s in sorted(office) if s in pdfs]


def payload(rec: dict) -> bytes | None:
    """HTTP body of one WARC response record (one gzip member at offset/length)."""
    raw = fetch(DATA + rec['warc'], {'Range': f"bytes={rec['offset']}-{rec['offset'] + rec['length'] - 1}"})
    data = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    parts = data.split(b'\r\n\r\n', 2)
    if len(parts) < 3:
        return None
    http_head, body = parts[1], parts[2]
    if re.search(rb'transfer-encoding:\s*chunked', http_head, re.I):
        out, p = bytearray(), 0
        while True:
            nl = body.find(b'\r\n', p)
            if nl < 0:
                break
            size = int(body[p:nl].split(b';')[0] or b'0', 16)
            if size == 0:
                break
            out += body[nl + 2:nl + 2 + size]
            p = nl + 2 + size + 2
        body = bytes(out)
    return body


def words(text: str) -> set[str]:
    import unicodedata
    return set(re.findall(r'\w{3,}', unicodedata.normalize('NFKC', text).lower()))


def same_document(doc: Path, ref: Path, work: Path) -> bool:
    """Name-matched files can be different documents: render the Office file with LibreOffice and
    require a compatible page count and at least 70% of its words in the reference PDF."""
    import os
    import shutil
    office = shutil.which('soffice') or shutil.which('libreoffice')
    if not office:
        return False
    env = {**os.environ, 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
    subprocess.run([office, f'-env:UserInstallation=file:///tmp/inkdos-lo-{os.getpid()}', '--headless', '--convert-to', 'pdf',
                    '--outdir', str(work), str(doc)], capture_output=True, timeout=300, env=env)
    lo = work / (doc.stem + '.pdf')
    if not lo.exists():
        return False
    pages = lambda f: int((re.search(r'^Pages:\s+(\d+)', subprocess.run(['pdfinfo', str(f)], capture_output=True, text=True).stdout, re.M) or [0, 0])[1])
    text = lambda f: subprocess.run(['pdftotext', str(f), '-'], capture_output=True, text=True).stdout
    a, b = words(text(lo)), words(text(ref))
    pa, pb = pages(lo), pages(ref)
    lo.unlink()
    if not a or not pa or not pb or abs(pa - pb) > max(1, 0.2 * pb):
        return False
    return len(a & b) / len(a) >= 0.7


def producer(pdf: Path) -> str:
    info = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    return ' / '.join(m.strip() for m in re.findall(r'^(?:Producer|Creator):\s*(.*)$', info, re.M))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--kind', choices=sorted(KINDS), default='presentations')
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--pairs', type=int, default=60, help='stop after this many verified pairs')
    ap.add_argument('--crawls', default=','.join(CRAWLS))
    ap.add_argument('--parts', type=int, default=300, help='index parts scanned per crawl')
    args = ap.parse_args()
    import duckdb
    kind = KINDS[args.kind]
    out = args.out / args.kind
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out / f'{args.kind}-manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    seen = {m['source'] for m in manifest}
    con = duckdb.connect()
    con.execute('INSTALL httpfs; LOAD httpfs;')
    for crawl in args.crawls.split(','):
        for part in index_parts(crawl)[:args.parts]:
            if len(manifest) >= args.pairs:
                break
            try:
                pairs = candidates(con, part, kind)
            except Exception as e:  # a transient read error skips one part
                print(f'skip {part}: {e}', file=sys.stderr)
                continue
            for doc, pdf in pairs:
                if len(manifest) >= args.pairs or doc['url'] in seen:
                    continue
                try:
                    body, ref = payload(doc), payload(pdf)
                except Exception:
                    continue
                if not body or not ref or not ref.startswith(b'%PDF'):
                    continue
                name = hashlib.sha1(doc['url'].encode()).hexdigest()[:12]
                ext = kind['mimes'][doc['mime']]
                tmp = out / f'{name}.pdf'
                tmp.write_bytes(ref)
                prod = producer(tmp)
                if not kind['producer'].search(prod):
                    tmp.unlink()
                    continue
                (out / f'{name}{ext}').write_bytes(body)
                work = out / '.verify'
                work.mkdir(exist_ok=True)
                if not same_document(out / f'{name}{ext}', tmp, work):
                    (out / f'{name}{ext}').unlink()
                    tmp.unlink()
                    continue
                manifest.append({'file': f'{args.kind}/{name}{ext}', 'reference': f'{args.kind}/{name}.pdf', 'source': doc['url'],
                                 'referenceSource': pdf['url'], 'producer': prod, 'crawl': crawl,
                                 'sha256': hashlib.sha256(body).hexdigest(), 'referenceSha256': hashlib.sha256(ref).hexdigest()})
                seen.add(doc['url'])
                manifest_path.write_text(json.dumps(manifest, indent=1), encoding='utf-8')
                print(f'{len(manifest)}: {doc["url"]}  [{prod}]', flush=True)
        if len(manifest) >= args.pairs:
            break
    print(f'{len(manifest)} verified pairs in {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
