#!/usr/bin/env python3
"""Acceptance criteria for Documents (DOC/DOCX/RTF), document by document.

Level 1 - nothing is lost:
  open      the document opens without a page error
  text      every word of the reference appears in the rendered pages (a few field results such as
            page numbers or dates may legitimately differ: up to max(3, 1%) of the words)
  images    the pages show at least as many pictures as the body and default header/footer carry
  tables    the pages show at least as many tables as the body carries
  save      saving without edits succeeds and, for a .docx, keeps the text of the body, headers,
            footers and notes exactly
Level 2 - structure is right:
  pages     page count within max(1, 10%) of the reference
  order     the words follow the reference order (sequence similarity >= 0.9)

The reference is a PDF next to the document (same stem; ideally exported by Word), else a
LibreOffice render. Pictures and tables are counted in the package (a .doc/.rtf is first converted
to .docx by LibreOffice). A per-page visual difference is reported for information only: pages
drift once line breaking differs, so it is not a pass/fail criterion. Inputs may be private
documents: nothing is written to the repository, the report goes to --out.

    python3 scripts/documents_acceptance.py letter.docx old.doc --out /tmp/doc-acceptance
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from presentations_acceptance import missing_words  # noqa: E402
from presentations_fidelity import ROOT, free_port, reference_pdf, run  # noqa: E402

CRITERIA = ('open', 'text', 'images', 'tables', 'save', 'pages', 'order')

# Rendered pages from the live app: text per page, pictures in the body and around it, tables.
PROBE = r"""() => { const pages=[...document.querySelectorAll('.doc-page')];
  const body=p=>p.querySelector('.page-content');
  return {pages:pages.length,
    // only text that is actually visible: a text node clipped away by its page counts as lost
    text:pages.map(p=>{const out=[],w=document.createTreeWalker(p,NodeFilter.SHOW_TEXT),r=document.createRange();
      for(let n=w.nextNode();n;n=w.nextNode()){if(!n.nodeValue.trim())continue;const clip=n.parentElement.closest('.page-content,.page-header,.page-footer')||p,c=clip.getBoundingClientRect();
        r.selectNodeContents(n);if([...r.getClientRects()].some(x=>x.width>0&&x.bottom>c.top+1&&x.top<c.bottom-1&&x.right>c.left+1&&x.left<c.right-1))out.push(n.nodeValue)}
      return out.join(' ')}),
    bodyImages:pages.reduce((n,p)=>n+(body(p)?body(p).querySelectorAll('img,svg image,canvas').length:0),0),
    edgeImages:pages[0]?[...pages[0].querySelectorAll('img')].filter(i=>!body(pages[0])?.contains(i)).length:0,
    tables:pages.reduce((n,p)=>n+(body(p)?body(p).querySelectorAll('table').length:0),0)} }"""


def words(text: str) -> list[str]:
    return re.findall(r'\w+', unicodedata.normalize('NFKC', text or '').lower().replace('­', ''))


def order_score(ref: list[str], got: list[str]) -> float:
    """Share of anchor words (present exactly once on both sides) that keep the reference order:
    longest increasing subsequence of their rendered positions, O(n log n)."""
    import bisect
    from collections import Counter
    cr, cg = Counter(ref), Counter(got)
    pos = {w: i for i, w in enumerate(got) if cg[w] == 1}
    seq = [pos[w] for w in ref if cr[w] == 1 and w in pos]
    if len(seq) < 5:
        return 1.0
    tails: list[int] = []
    for x in seq:
        k = bisect.bisect_left(tails, x)
        tails[k:k + 1] = [x]
    return len(tails) / len(seq)


def source_package(src: Path, work: Path) -> Path | None:
    if src.suffix.lower() == '.docx':
        return src
    soffice = shutil.which('soffice') or shutil.which('libreoffice')
    if not soffice:
        return None
    run([soffice, '--headless', '--convert-to', 'docx', '--outdir', str(work), str(src)], timeout=300)
    conv = work / (src.stem + '.docx')
    return conv if conv.exists() else None


def package_counts(docx: Path) -> dict:
    """Pictures and tables the package carries: body, plus the most pictured header and footer."""
    try:
        z = zipfile.ZipFile(docx)
        names = z.namelist()
        read = lambda n: re.sub(rb'<mc:Fallback>.*?</mc:Fallback>', b'', z.read(n), flags=re.S)
        pics = lambda x: len(re.findall(rb'<a:blip\b[^>]*r:embed=|<v:imagedata\b[^>]*r:id=', x))
        doc = read('word/document.xml')
        edge = sum(max([pics(read(n)) for n in names if re.fullmatch(rf'word/{k}\d*\.xml', n)] or [0]) for k in ('header', 'footer'))
        return {'bodyImages': pics(doc), 'edgeImages': edge, 'tables': len(re.findall(rb'<w:tbl>', doc))}
    except (zipfile.BadZipFile, KeyError, OSError):
        return {}


# Save as the Save command does, without edits; the result comes back base64-encoded.
SAVE = r"""async legacy => { const NS=globalThis.InkDOS2Documents, s=NS.DocumentsDebug.session;
  // a .doc/.rtf is saved as a new DOCX copy, a .docx is patched in place (as the Save command does)
  const r=await NS.DocxWriter.save(document.getElementById('pagesHost'), 'saved.docx', legacy?null:s.sourceBuffer, legacy?null:s.sourceContext);
  const u=new Uint8Array(await r.blob.arrayBuffer()); let t=''; for(let i=0;i<u.length;i+=32768) t+=String.fromCharCode(...u.subarray(i,i+32768)); return btoa(t) }"""


def package_text(data: bytes) -> dict[str, str] | None:
    """Text runs of the parts a reader sees: body, headers, footers, foot/endnotes."""
    import html as html_mod
    import io
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        runs = lambda n: b''.join(re.findall(rb'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', z.read(n))).decode('utf-8', 'replace')
        return {n: html_mod.unescape(runs(n)) for n in z.namelist()
                if re.fullmatch(r'word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml', n)}
    except (zipfile.BadZipFile, KeyError):
        return None


def save_check(page, src: Path) -> str:
    """'' when saving keeps everything, else what went wrong."""
    import base64
    try:
        saved = base64.b64decode(page.evaluate(SAVE, src.suffix.lower() != '.docx'))
    except Exception as e:
        return 'save failed: ' + str(e).splitlines()[0][:160]
    after = package_text(saved)
    if after is None:
        return 'saved file is not a readable .docx'
    if src.suffix.lower() != '.docx':
        return ''
    before = package_text(src.read_bytes()) or {}
    changed = [n for n, t in before.items() if after.get(n) != t]
    return ('text changed in ' + ', '.join(changed)) if changed else ''


def pdf_pages(pdf: Path) -> int:
    m = re.search(r'Pages:\s+(\d+)', run(['pdfinfo', str(pdf)]).stdout)
    return int(m.group(1)) if m else 0


def check_document(page, src: Path, work: Path, *, pdf: Path | None) -> dict:
    failed = {c: 0 for c in CRITERIA}
    if not pdf:
        return {'file': src.name, 'skipped': True, 'failed': failed}
    ref_pages = pdf_pages(pdf)
    ref_text = run(['pdftotext', '-enc', 'UTF-8', str(pdf), '-']).stdout
    if not ref_pages or not words(ref_text):
        return {'file': src.name, 'skipped': True, 'failed': failed}
    page.set_input_files('#fileInput', str(src))
    opened = "n=>document.title.startsWith(n)&&document.querySelectorAll('.doc-page').length>0"
    page.wait_for_function(f"n=>({opened})(n)||/failed|error/i.test(document.getElementById('statusText')?.textContent||'')", arg=src.name, timeout=120000)
    if not page.evaluate(f"n=>({opened})(n)", src.name):
        failed['open'] = 1
        return {'file': src.name, 'failed': failed, 'refPages': ref_pages}
    last, stable = -1, 0
    for _ in range(40):  # pagination settles asynchronously
        page.wait_for_timeout(250)
        n = page.evaluate("()=>document.querySelectorAll('.doc-page').length")
        stable = stable + 1 if n == last else 0
        last = n
        if stable >= 4:
            break
    got = page.evaluate(PROBE)
    app_text = '\n'.join(got['text'])
    missing = missing_words(ref_text, app_text)
    ref_words = words(ref_text)
    if len(missing) > max(3, len(ref_words) // 100):
        failed['text'] = 1
    pkg = source_package(src, work)
    counts = package_counts(pkg) if pkg else {}
    if counts and got['bodyImages'] + got['edgeImages'] < counts['bodyImages'] + counts['edgeImages']:
        failed['images'] = 1
    if counts and got['tables'] < counts['tables']:
        failed['tables'] = 1
    saved = save_check(page, src)
    if saved:
        failed['save'] = 1
    if abs(got['pages'] - ref_pages) > max(1, round(ref_pages * 0.1)):
        failed['pages'] = 1
    order = order_score(ref_words, words(app_text))
    if order < 0.9:
        failed['order'] = 1
    return {'file': src.name, 'failed': failed, 'pages': got['pages'], 'refPages': ref_pages, 'words': len(ref_words),
            'missing': missing[:60], 'missingCount': len(missing), 'order': round(order, 3),
            'images': [got['bodyImages'], got['edgeImages']], 'refImages': [counts.get('bodyImages'), counts.get('edgeImages')],
            'tables': got['tables'], 'refTables': counts.get('tables'), 'save': saved, 'reference': 'pdf' if pdf == src.with_suffix('.pdf') else 'libreoffice'}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+', type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--chromium', default='/opt/pw-browsers/chromium')
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright
    if not shutil.which('pdftotext'):
        print('pdftotext (poppler-utils) is required', file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    port = free_port()
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    report = []
    try:
        with sync_playwright() as pw:
            launch = {'headless': True}
            if Path(args.chromium).exists():
                launch['executable_path'] = args.chromium
            browser = pw.chromium.launch(**launch)
            for src in args.files:
                src = src.resolve()
                if src.suffix.lower() not in ('.doc', '.docx', '.rtf'):
                    continue
                work = args.out / f'{src.stem}-{src.suffix.lstrip(".").lower()}'
                work.mkdir(parents=True, exist_ok=True)
                ctx = browser.new_context(service_workers='block', viewport={'width': 1300, 'height': 900})
                page = ctx.new_page()
                errors: list[str] = []
                page.on('pageerror', lambda e: errors.append(str(e)[:200]))
                try:
                    page.goto(f'http://127.0.0.1:{port}/apps/documents/', wait_until='load')
                    page.wait_for_function("()=>!!globalThis.InkDOS2Documents?.DocumentsDebug", timeout=30000)
                    r = check_document(page, src, work, pdf=reference_pdf(src, work))
                except Exception as e:
                    r = {'file': src.name, 'failed': {'open': 1}, 'error': str(e)[:200]}
                finally:
                    ctx.close()
                if errors:
                    r['errors'] = errors[:5]
                    r['failed']['open'] = 1
                report.append(r)
                bad = 'skipped (reference cannot read it)' if r.get('skipped') else (', '.join(f'{c}' for c, n in r['failed'].items() if n) or 'all criteria pass')
                print(f"{r['file']}: {r.get('pages', '?')}/{r.get('refPages', '?')} pages - {bad}", flush=True)
            browser.close()
    finally:
        server.terminate()
    (args.out / 'documents-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return 1 if any(any(r['failed'].values()) for r in report) else 0


if __name__ == '__main__':
    sys.exit(main())
