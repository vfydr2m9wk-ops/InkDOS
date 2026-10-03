#!/usr/bin/env python3
"""Download a reproducible corpus of public office files and PDFs for acceptance testing.

Sources (files go to --out, never into the repository; only this script is versioned):
  poi        Apache POI test data at a pinned commit: format edge cases (slideshow, spreadsheet, document).
  bugzilla   LibreOffice Bugzilla attachments - real files that broke an importer.
  pdfjs      pdf.js test/pdfs at a pinned commit: hard PDF cases (--kind pdf).
  govdocs    Govdocs1 (Digital Corpora) real-world .ppt/.xls/.doc/.pdf files. Only the index of each
             zip archive and the selected members are fetched (HTTP range requests).

Selection is deterministic (pinned commit, ascending ids, fixed archives), and manifest.json
records source, URL and SHA-256 for every file.

    python3 scripts/presentations_public_corpus.py --kind presentations --out /tmp/inkdos-public
    python3 scripts/presentations_public_corpus.py --kind pdf --sources pdfjs,govdocs --out /tmp/inkdos-pdf
    python3 scripts/presentations_acceptance.py /tmp/inkdos-public/*/* --out /tmp/acceptance
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

POI_COMMIT = '732120980140d5ed64b482c470e0b625cdb1ab15'
PDFJS_COMMIT = '2581d8f70add6f945cee6f61425c2ae40009bd8d'
KINDS = {
    'presentations': {'exts': ('.ppt', '.pptx'), 'poi': 'test-data/slideshow',
                      'mime': {'application/vnd.ms-powerpoint': '.ppt',
                               'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx'}},
    'spreadsheets': {'exts': ('.xls', '.xlsx'), 'poi': 'test-data/spreadsheet',
                     'mime': {'application/vnd.ms-excel': '.xls',
                              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx'}},
    'documents': {'exts': ('.doc', '.docx'), 'poi': 'test-data/document',
                  'mime': {'application/msword': '.doc',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'}},
    'pdf': {'exts': ('.pdf',), 'poi': None, 'mime': {'application/pdf': '.pdf'}},
}
BUGZILLA = 'https://bugs.documentfoundation.org'
GOVDOCS = 'https://digitalcorpora.s3.amazonaws.com/corpora/files/govdocs1/zipfiles/{:03d}.zip'
UA = {'User-Agent': 'InkDOS-corpus/1 (+fidelity testing)'}


def fetch(url: str, headers: dict | None = None, timeout: int = 120) -> bytes:
    """GET with a polite pause and retries on rate limiting (Bugzilla answers 503/429 when hurried)."""
    import time
    import urllib.error
    for attempt in range(5):
        req = urllib.request.Request(url, headers={**UA, **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            if 'documentfoundation' in url:
                time.sleep(1.0)
            return data
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(url)


def save(out: Path, name: str, data: bytes, source: str, url: str, manifest: list) -> None:
    path = out / name
    path.write_bytes(data)
    manifest.append({'source': source, 'file': f'{out.name}/{name}', 'url': url, 'bytes': len(data),
                     'sha256': hashlib.sha256(data).hexdigest()})


def sparse_repo(work: Path, url: str, commit: str, folder: str) -> Path:
    if not work.exists():
        subprocess.run(['git', 'init', '-q', str(work)], check=True)
        subprocess.run(['git', '-C', str(work), 'remote', 'add', 'origin', url], check=True)
        subprocess.run(['git', '-C', str(work), 'sparse-checkout', 'set', folder], check=True)
        subprocess.run(['git', '-C', str(work), 'fetch', '-q', '--depth', '1', '--filter=blob:none', 'origin', commit], check=True)
        subprocess.run(['git', '-C', str(work), 'checkout', '-q', 'FETCH_HEAD'], check=True)
    return work / folder


def poi(out: Path, limit: int, manifest: list, kind: dict) -> None:
    if not kind['poi']:
        return
    folder = sparse_repo(out / '.git-poi', 'https://github.com/apache/poi', POI_COMMIT, kind['poi'])
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in kind['exts'])
    for p in files[:limit]:
        save(out, p.name, p.read_bytes(), 'poi', f'https://github.com/apache/poi/blob/{POI_COMMIT}/{kind["poi"]}/{p.name}', manifest)


def pdfjs(out: Path, limit: int, manifest: list, kind: dict) -> None:
    """pdf.js test PDFs kept in the repository (the .link ones point elsewhere and are skipped)."""
    if '.pdf' not in kind['exts']:
        return
    folder = sparse_repo(out / '.git-pdfjs', 'https://github.com/mozilla/pdf.js', PDFJS_COMMIT, 'test/pdfs')
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == '.pdf')
    for p in files[:limit]:
        save(out, p.name, p.read_bytes(), 'pdfjs', f'https://github.com/mozilla/pdf.js/blob/{PDFJS_COMMIT}/test/pdfs/{p.name}', manifest)


def bugzilla(out: Path, limit: int, manifest: list, kind: dict) -> None:
    got = 0
    for mime, ext in kind['mime'].items():
        q = urllib.parse.urlencode({'f1': 'attachments.mimetype', 'o1': 'equals', 'v1': mime, 'include_fields': 'id',
                                    'order': 'bug_id', 'limit': limit * 2})
        bugs = [b['id'] for b in json.loads(fetch(f'{BUGZILLA}/rest/bug?{q}'))['bugs']]
        for bug in sorted(bugs):
            if got >= limit:
                return
            meta = json.loads(fetch(f'{BUGZILLA}/rest/bug/{bug}/attachment?exclude_fields=data'))
            for a in sorted(meta['bugs'].get(str(bug), []), key=lambda a: a['id']):
                if a.get('is_private') or a.get('is_obsolete') or a.get('content_type') != mime or a.get('size', 0) > 20_000_000:
                    continue
                url = f'{BUGZILLA}/attachment.cgi?id={a["id"]}'
                try:
                    data = fetch(url)
                except Exception as e:  # deleted or restricted attachments
                    print(f'skip {url}: {e}', file=sys.stderr)
                    continue
                save(out, f'tdf{bug}-{a["id"]}{ext}', data, 'bugzilla', url, manifest)
                got += 1
                break  # one deck per bug keeps the corpus varied


def remote_zip_members(url: str):
    """Central directory of a remote zip via range requests: (name, offset, csize, method)."""
    tail = fetch(url, {'Range': 'bytes=-131072'})
    i = tail.rfind(b'PK\x05\x06')
    if i < 0:
        raise ValueError('end of central directory not found')
    count, cd_size, cd_off = struct.unpack('<HII', tail[i + 10:i + 20])
    if cd_off == 0xffffffff:  # zip64
        j = tail.rfind(b'PK\x06\x06')
        cd_size, cd_off = struct.unpack('<QQ', tail[j + 40:j + 56])
    cd = fetch(url, {'Range': f'bytes={cd_off}-{cd_off + cd_size - 1}'})
    p = 0
    while p + 46 <= len(cd) and cd[p:p + 4] == b'PK\x01\x02':
        method, = struct.unpack('<H', cd[p + 10:p + 12])
        csize, usize = struct.unpack('<II', cd[p + 20:p + 28])
        nlen, xlen, clen = struct.unpack('<HHH', cd[p + 28:p + 34])
        off, = struct.unpack('<I', cd[p + 42:p + 46])
        name = cd[p + 46:p + 46 + nlen].decode('utf-8', 'replace')
        if 0xffffffff in (csize, usize, off):
            extra = cd[p + 46 + nlen:p + 46 + nlen + xlen]
            k = 0
            while k + 4 <= len(extra):
                hid, hlen = struct.unpack('<HH', extra[k:k + 4])
                if hid == 1:
                    vals, q = list(struct.unpack(f'<{hlen // 8}Q', extra[k + 4:k + 4 + (hlen // 8) * 8])), 0
                    if usize == 0xffffffff:
                        usize, q = vals[q], q + 1
                    if csize == 0xffffffff:
                        csize, q = vals[q], q + 1
                    if off == 0xffffffff:
                        off = vals[q]
                k += 4 + hlen
        yield name, off, csize, method
        p += 46 + nlen + xlen + clen


def govdocs(out: Path, limit: int, manifest: list, kind: dict) -> None:
    got = 0
    for n in range(0, 1000):
        if got >= limit:
            return
        url = GOVDOCS.format(n)
        members = sorted(m for m in remote_zip_members(url) if m[0].lower().endswith(kind['exts']))
        for name, off, csize, method in members:
            if got >= limit:
                return
            head = fetch(url, {'Range': f'bytes={off}-{off + 29}'})
            nlen, xlen = struct.unpack('<HH', head[26:30])
            start = off + 30 + nlen + xlen
            data = fetch(url, {'Range': f'bytes={start}-{start + csize - 1}'})
            if method == 8:
                data = zlib.decompress(data, -15)
            elif method != 0:
                continue
            save(out, Path(name).name, data, 'govdocs', f'{url}#{name}', manifest)
            got += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--kind', choices=sorted(KINDS), default='presentations')
    ap.add_argument('--sources', default='poi,bugzilla,govdocs', help='poi, bugzilla, govdocs, pdfjs')
    ap.add_argument('--limit', type=int, default=150, help='files per source')
    args = ap.parse_args()
    manifest: list = []
    for src in args.sources.split(','):
        out = args.out / src
        out.mkdir(parents=True, exist_ok=True)
        {'poi': poi, 'bugzilla': bugzilla, 'govdocs': govdocs, 'pdfjs': pdfjs}[src](out, args.limit, manifest, KINDS[args.kind])
        print(f'{src}: {sum(1 for m in manifest if m["source"] == src)} files')
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
