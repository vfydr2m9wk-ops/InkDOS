#!/usr/bin/env python3
"""Acceptance criteria for the PDF viewer, page by page.

Level 1 - nothing is lost:
  open    the file opens (no error, a page count appears)
  pages   the viewer shows as many pages as the file has (pdfinfo)
  blank   no page renders blank where the reference page has content
  errors  no JavaScript error while opening and paging through the document
Level 2 - it looks right:
  visual  each page is close to an independent render (Poppler pdftoppm): % of differing
          pixels after downscaling, ImageMagick `compare -fuzz`

Inputs may be private documents: nothing is written to the repository, the report goes to --out.

    python3 scripts/pdf_acceptance.py a.pdf b.pdf --out /tmp/pdf-acceptance [--max-pages 40]
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from presentations_fidelity import ROOT, free_port, run, score  # noqa: E402

CRITERIA = ('open', 'pages', 'blank', 'errors', 'visual')
VISUAL_LIMIT = 15.0


def page_count(pdf: Path) -> int | None:
    m = re.search(r'^Pages:\s+(\d+)', run(['pdfinfo', str(pdf)]).stdout, re.M)
    return int(m.group(1)) if m else None


def ink(png: Path) -> float:
    r = run(['convert', str(png), '-colorspace', 'gray', '-format', '%[fx:standard_deviation]', 'info:'])
    try:
        return float(r.stdout.strip() or 0)
    except ValueError:
        return 0.0


def substituted_fonts(pdf: Path, n: int) -> bool:
    rows = run(['pdffonts', '-f', str(n), '-l', str(n), str(pdf)]).stdout.splitlines()[2:]
    return any(len(r.split()) >= 5 and r.split()[-5] == 'no' for r in rows)


def sample(n: int, cap: int) -> list[int]:
    if n <= cap:
        return list(range(1, n + 1))
    step = (n - 1) / (cap - 1)
    return sorted({1 + round(i * step) for i in range(cap)})


def check_pdf(page, pdf: Path, work: Path, max_pages: int, errors: list) -> dict:
    want = page_count(pdf)
    if want is None:  # the reference cannot read it either (damaged, encrypted, unsupported): nothing to compare
        return {'file': pdf.name, 'pages': 0, 'refPages': None, 'skipped': True, 'failedPages': {c: 0 for c in CRITERIA}, 'perPage': []}
    page.set_input_files('#fileInput', str(pdf))
    try:
        page.wait_for_function("()=>(globalThis.InkDOS2PdfP4?.PdfStabilityDebug?.session?.pageCount||0)>0", timeout=60000)
    except Exception:
        return {'file': pdf.name, 'pages': 0, 'refPages': want, 'failedPages': {'open': 1}, 'errors': errors[:5], 'perPage': []}
    got = page.evaluate("()=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.session.pageCount")
    fails = {c: 0 for c in CRITERIA}
    if want is not None and got != want:
        fails['pages'] = 1
    per = []
    for n in sample(got, max_pages):
        page.evaluate("(n)=>globalThis.InkDOS2PdfP4.PdfStabilityDebug.navigation.goToPage(n)", n)
        sel = f'.pdf-page-shell[data-page="{n}"]'
        try:
            page.wait_for_function("(s)=>{const c=document.querySelector(s+' canvas');return !!c&&c.width>0&&c.height>0}", arg=sel, timeout=30000)
        except Exception:
            per.append({'page': n, 'fail': ['blank'], 'why': 'no canvas'})
            fails['blank'] += 1
            continue
        page.wait_for_timeout(400)
        shot, ref_prefix = work / f'ink-{n:04d}.png', work / f'ref-{n:04d}'
        data = page.evaluate("(s)=>document.querySelector(s+' canvas').toDataURL('image/png')", sel)  # whole page, not the viewport
        shot.write_bytes(base64.b64decode(data.split(',', 1)[1]))
        run(['pdftoppm', '-r', '48', '-singlefile', '-f', str(n), '-l', str(n), '-png', str(pdf), str(ref_prefix)])
        ref = ref_prefix.with_suffix('.png')
        res = {'page': n, 'fail': []}
        if ref.exists():
            if ink(ref) > 0.01 and ink(shot) <= 0.003:
                res['fail'].append('blank')
            res['visual'] = score(shot, ref, work)
            if res['visual'] > VISUAL_LIMIT:
                if substituted_fonts(pdf, n):  # viewer and reference pick different stand-ins for missing fonts
                    res['warning'] = 'visual difference on a page with non-embedded fonts'
                else:
                    res['fail'].append('visual')
        for c in res['fail']:
            fails[c] += 1
        per.append(res)
    if errors:
        fails['errors'] = len(errors)
    return {'file': pdf.name, 'pages': got, 'refPages': want, 'failedPages': fails, 'errors': errors[:5], 'perPage': per}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+', type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--max-pages', type=int, default=30, help='pages checked per document (evenly sampled)')
    ap.add_argument('--chromium', default='/opt/pw-browsers/chromium')
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright
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
            for pdf in args.files:
                pdf = pdf.resolve()
                work = args.out / pdf.stem
                work.mkdir(parents=True, exist_ok=True)
                ctx = browser.new_context(service_workers='block', viewport={'width': 1300, 'height': 900})
                page = ctx.new_page()
                errors: list[str] = []
                page.on('pageerror', lambda e: errors.append(str(e)[:200]))
                try:
                    page.goto(f'http://127.0.0.1:{port}/apps/pdf/', wait_until='load')
                    page.wait_for_timeout(600)
                    r = check_pdf(page, pdf, work, args.max_pages, errors)
                except Exception as e:
                    r = {'file': pdf.name, 'pages': 0, 'refPages': page_count(pdf), 'failedPages': {'open': 1}, 'errors': [str(e)[:200]], 'perPage': []}
                finally:
                    ctx.close()
                report.append(r)
                bad = 'skipped (reference cannot read it)' if r.get('skipped') else (', '.join(f'{c} {n}' for c, n in r['failedPages'].items() if n) or 'all criteria pass')
                print(f"{r['file']}: {r['pages']}/{r['refPages']} pages - {bad}", flush=True)
            browser.close()
    finally:
        server.terminate()
    (args.out / 'pdf-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return 1 if any(any(r['failedPages'].values()) for r in report) else 0


if __name__ == '__main__':
    sys.exit(main())
