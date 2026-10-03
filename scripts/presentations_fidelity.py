#!/usr/bin/env python3
"""Measure Presentations rendering fidelity against a reference, slide by slide.

For each .ppt/.pptx given, the reference is a PDF next to it (same stem; ideally
exported by Microsoft PowerPoint) or, when absent, a LibreOffice render. InkDOS
slides are captured from the real app in Chromium. Each slide gets a difference
score (% of differing pixels after downscaling, ImageMagick `compare -fuzz`), and
.ppt files also report the legacy reader's coverage diagnostics.

Outputs report.json and report.html (side-by-side, worst slides first) in --out.
Local tool: inputs may be private documents, so nothing is written to the repo.

    python3 scripts/presentations_fidelity.py deck.ppt other.pptx --out /tmp/fid
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THUMB = '320x240!'


def free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kw)


def reference_pdf(src: Path, work: Path) -> Path | None:
    own = src.with_suffix('.pdf')
    if own.exists():
        return own
    soffice = shutil.which('soffice') or shutil.which('libreoffice')
    if not soffice:
        return None
    run([soffice, '--headless', '--convert-to', 'pdf', '--outdir', str(work), str(src)], timeout=300)
    out = work / (src.stem + '.pdf')
    return out if out.exists() else None


def score(a: Path, b: Path, work: Path) -> float:
    sa, sb = work / 'a.png', work / 'b.png'
    run(['convert', str(a), '-resize', THUMB, '-colorspace', 'gray', str(sa)])
    run(['convert', str(b), '-resize', THUMB, '-colorspace', 'gray', str(sb)])
    r = run(['compare', '-metric', 'AE', '-fuzz', '12%', str(sa), str(sb), 'null:'])
    try:
        diff = float((r.stderr or '0').split()[0])
    except ValueError:
        return 100.0
    return round(100 * diff / (320 * 240), 2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+', type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--chromium', default=os.environ.get('CHROMIUM_PATH', '/opt/pw-browsers/chromium'))
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright

    args.out.mkdir(parents=True, exist_ok=True)
    port = free_port()
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report = []
    try:
        time.sleep(0.8)
        with sync_playwright() as pw:
            launch = {'headless': True}
            if args.chromium and Path(args.chromium).exists():
                launch['executable_path'] = args.chromium
            browser = pw.chromium.launch(**launch)
            for src in args.files:
                src = src.resolve()
                work = args.out / src.stem
                work.mkdir(parents=True, exist_ok=True)
                pdf = reference_pdf(src, work)
                ctx = browser.new_context(service_workers='block', viewport={'width': 1400, 'height': 900})
                page = ctx.new_page()
                page.goto(f'http://127.0.0.1:{port}/apps/presentations/', wait_until='load')
                page.wait_for_timeout(800)
                page.set_input_files('#fileInput', str(src))
                page.wait_for_function("() => document.querySelectorAll('.slide-thumb').length > 0", timeout=120000)
                page.wait_for_timeout(1500)
                diagnostics = None
                if src.suffix.lower() == '.ppt':
                    b64 = base64.b64encode(src.read_bytes()).decode()
                    diagnostics = page.evaluate("""(b64)=>{const s=atob(b64),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);
                        try{return globalThis.InkDOS2Presentations.PptLegacyReader.decode(u.buffer).diagnostics||null}catch(e){return {error:String(e)}}}""", b64)
                count = page.locator('.slide-thumb').count()
                if pdf:
                    run(['pdftoppm', '-r', '48', '-png', str(pdf), str(work / 'ref')])
                refs = sorted(work.glob('ref-*.png'))
                slides = []
                for n in range(1, count + 1):
                    page.locator('.slide-thumb').nth(n - 1).click()
                    page.wait_for_timeout(500)
                    shot = work / f'ink-{n:03d}.png'
                    page.locator('#slideCanvas').first.screenshot(path=str(shot))
                    ref = refs[n - 1] if n - 1 < len(refs) else None
                    slides.append({'slide': n, 'score': score(shot, ref, work) if ref else None,
                                   'ink': str(shot.relative_to(args.out)), 'ref': str(ref.relative_to(args.out)) if ref else None})
                ctx.close()
                scored = [s['score'] for s in slides if s['score'] is not None]
                report.append({'file': src.name, 'reference': 'pdf' if pdf and pdf.parent != work else ('libreoffice' if pdf else None),
                               'slides': slides, 'meanScore': round(sum(scored) / len(scored), 2) if scored else None,
                               'diagnostics': diagnostics})
                print(f"{src.name}: {count} slides, mean difference {report[-1]['meanScore']}%")
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    (args.out / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    rows = []
    for deck in report:
        rows.append(f"<h2>{html.escape(deck['file'])} — mean {deck['meanScore']}% (reference: {deck['reference']})</h2>")
        if deck['diagnostics']:
            rows.append(f"<pre>{html.escape(json.dumps(deck['diagnostics'], ensure_ascii=False))}</pre>")
        for s in sorted(deck['slides'], key=lambda s: -(s['score'] or 0)):
            ref = f"<img src='{html.escape(s['ref'])}'>" if s['ref'] else '<i>no reference</i>'
            rows.append(f"<div class=row><b>slide {s['slide']} · {s['score']}%</b><div>{ref}<img src='{html.escape(s['ink'])}'></div></div>")
    (args.out / 'report.html').write_text(
        "<!doctype html><meta charset=utf-8><title>Presentations fidelity</title><style>body{font:14px system-ui;margin:16px}"
        "img{width:400px;border:1px solid #ccc;margin-right:6px}.row{margin:10px 0}pre{white-space:pre-wrap;background:#f4f4f4;padding:8px}</style>"
        "<p>Left: reference · Right: InkDOS · worst slides first</p>" + ''.join(rows), encoding='utf-8')
    print(args.out / 'report.html')
    return 0


if __name__ == '__main__':
    sys.exit(main())
