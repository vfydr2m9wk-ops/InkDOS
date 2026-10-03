#!/usr/bin/env python3
"""Acceptance criteria for Presentations rendering, slide by slide.

Level 1 - nothing is lost:
  slides    the deck shows as many slides as the reference
  text      every word of the reference slide appears in the rendered slide
  images    the slide shows at least as many pictures as the reference
  hidden    no text run is invisible (text colour equal to what is behind it)
            or covered by an opaque shape/picture drawn above it
  offslide  no text box lies mostly outside the slide
Level 2 - structure is right:
  background  the slide corners have the reference colour

The reference is a PDF next to the deck (same stem; ideally exported by PowerPoint). Without one,
the expectations come from the package itself (text of shapes, SmartArt and charts; pictures), so
public corpora without PDFs can be checked too; --libreoffice compares against a LibreOffice render
instead. Inputs may be private documents: nothing is written to the repository, the report goes
to --out.

    python3 scripts/presentations_acceptance.py deck.pptx other.ppt --out /tmp/acceptance

Exit status is 1 when any criterion fails. `check_deck` is also used by the repository
test with expectations taken from synthetic decks instead of a PDF.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from presentations_fidelity import ROOT, free_port, reference_pdf, run  # noqa: E402

CRITERIA = ('open', 'slides', 'text', 'images', 'hidden', 'offslide', 'background')

# Rendered-slide facts from the live app: text, pictures, invisible/covered runs, off-slide boxes.
PROBE = r"""() => {
  const app=globalThis.__inkdosPresentations, slide=app.session.currentSlide, canvas=document.getElementById('slideCanvas');
  const cr=canvas.getBoundingClientRect(), objs=[...(slide.templateObjects||[]),...slide.objects], order=new Map(objs.map((o,i)=>[o.id,i]));
  const el=id=>canvas.querySelector(`[data-object-id="${CSS.escape(id)}"]`);
  const rgb=s=>{const h=String(s||'').match(/^#([0-9a-f]{6})$/i);if(h)return [0,2,4].map(i=>parseInt(h[1].slice(i,i+2),16));const m=String(s||'').match(/[\d.]+/g);return m&&m.length>=3?m.slice(0,3).map(Number):null};
  const lum=c=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2])};
  const contrast=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
  const inside=(r,x,y)=>x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom;
  const opaque=o=>o&&(o.opacity??1)>.3&&(o.type==='image'||(o.type==='shape'&&(o.fill||o.fillGradient)&&(o.fillOpacity??1)>.3&&['rect','roundRect'].includes(o.shapeType)));
  const hidden=[],offslide=[],authored=[];
  for(const box of canvas.querySelectorAll('.slide-textbox')){
    const own=objs.find(o=>o.id===box.dataset.objectId),r=box.getBoundingClientRect(),txt=box.innerText.trim();
    if(!txt||!r.width||!r.height)continue;
    const ix=Math.max(0,Math.min(r.right,cr.right)-Math.max(r.left,cr.left)),iy=Math.max(0,Math.min(r.bottom,cr.bottom)-Math.max(r.top,cr.top));
    if(ix*iy<.5*r.width*r.height)offslide.push(txt.slice(0,60));
    const mine=order.get(own?.id)??-1;
    for(const s of box.querySelectorAll('.slide-paragraph > span:not(.slide-bullet)')){
      const t=s.textContent.trim();if(!/[\p{L}\p{N}]/u.test(t))continue;const sr=s.getClientRects()[0];if(!sr)continue;
      const x=sr.left+Math.min(sr.width/2,10),y=sr.top+sr.height/2;if(!inside(cr,x,y))continue;
      const over=objs.slice(mine+1).find(o=>opaque(o)&&el(o.id)&&inside(el(o.id).getBoundingClientRect(),x,y));
      if(over){hidden.push({text:t.slice(0,60),why:'covered by '+over.type});continue}
      const ownPainted=own&&(own.fill||own.fillGradient)&&(!own.geometry||[...box.querySelectorAll('.slide-text-geometry path,.slide-text-geometry image')].some(n=>n.tagName==='image'||(n.getAttribute('fill')||'none')!=='none')),under=(ownPainted?own:null)||objs.slice(0,Math.max(0,mine)).reverse().find(o=>(o.type==='image'||(o.type==='shape'&&(o.fill||o.fillGradient||o.fillImage)))&&el(o.id)&&inside(el(o.id).getBoundingClientRect(),x,y));
      let bg=null;if(!under){if(!slide.backgroundImage&&!slide.backgroundGradient)bg=rgb(slide.background||'#ffffff')}else if((under===own||(under.type==='shape'&&['rect','roundRect'].includes(under.shapeType)))&&under.fill&&!under.fillGradient&&!under.fillImage&&(under.fillOpacity??1)>.9)bg=rgb(under.fill);
      const fg=rgb(getComputedStyle(s).color);
      if(bg&&fg&&contrast(fg,bg)<1.05)(under===own&&own.fill&&rgb(own.fill).join()===fg.join()?authored:hidden).push({text:t.slice(0,60),why:`colour ${getComputedStyle(s).color} on rgb(${bg.join(', ')})${under?' ('+under.type+' '+(under.shapeType||'')+')':' (slide background)'}`});
    }
  }
  const images=[...canvas.querySelectorAll('.slide-image img')].filter(i=>i.complete&&i.naturalWidth>0&&i.getBoundingClientRect().width>1).length+(slide.backgroundImage?1:0)+canvas.querySelectorAll('pattern image').length+[...canvas.querySelectorAll('.slide-shape')].filter(e=>/url\(/.test(e.style.backgroundImage||'')).length;
  const text=[...canvas.querySelectorAll('.slide-textbox,.slide-table')].map(b=>b.innerText).join('\n');
  return {text,images,hidden,offslide,authored};
}"""


def missing_words(want: str, got: str) -> list[str]:
    """Reference words absent from the rendered text. PDF extraction joins words split at a line-end
    hyphen ("deixá-los" -> "deixálos") and can split a word around an accent; a token counts as present
    when it equals adjacent tokens joined on the other side."""
    norm = lambda t: re.findall(r'\w+', unicodedata.normalize('NFKC', t or '').lower().replace('\u00ad', ''))
    ref, ink = norm(want), norm(got)
    joined = lambda seq: {''.join(seq[i:i + k]) for k in (2, 3) for i in range(len(seq) - k + 1)}
    ink_joined, ref_joined = joined(ink), joined(ref)
    missing = Counter(ref) - Counter(ink)
    letters = Counter(''.join(ink))
    for w in list(missing):
        if w in ink_joined or any(w in j and j in set(ink) for j in ref_joined):
            del missing[w]
        elif len(w) == 1 and letters[w] >= missing[w]:
            del missing[w]  # stacked/one-letter lines: PDF yields one token per letter
    return sorted(missing.elements())


def pdf_page_text(pdf: Path, n: int) -> str:
    return run(['pdftotext', '-f', str(n), '-l', str(n), '-enc', 'UTF-8', str(pdf), '-']).stdout


def pptx_slide_images(pptx: Path) -> list[int]:
    """Pictures each slide shows, read from the package itself (independent of the InkDOS reader):
    p:pic and picture-filled shapes on the slide, plus the non-placeholder ones of its layout and
    master while they are shown (showMasterSp), plus a picture background. A PowerPoint PDF is not
    used for this: it rasterises shadows and effects into extra images."""
    import posixpath
    import zipfile
    z = zipfile.ZipFile(pptx)
    names = set(z.namelist())

    def xml(part):
        return z.read(part).decode('utf8', 'ignore') if part in names else ''

    def rel(part, kind):
        d, b = posixpath.split(part)
        r = xml(f'{d}/_rels/{b}.rels')
        m = re.search(r'Type="[^"]*/' + kind + r'"[^>]*Target="([^"]+)"', r) or re.search(r'Target="([^"]+)"[^>]*Type="[^"]*/' + kind + '"', r)
        return posixpath.normpath(posixpath.join(d, m.group(1))) if m else None

    def media_hash(part, rid):
        d, b = posixpath.split(part)
        r = xml(f'{d}/_rels/{b}.rels')
        m = re.search(r'Id="' + re.escape(rid) + r'"[^>]*Target="([^"]+)"', r) or re.search(r'Target="([^"]+)"[^>]*Id="' + re.escape(rid) + '"', r)
        target = posixpath.normpath(posixpath.join(d, m.group(1))) if m else None
        import hashlib
        return hashlib.sha1(z.read(target)).hexdigest() if target in names else rid

    def drawn(x, template, part=''):
        x = re.sub(r'<mc:Fallback>.*?</mc:Fallback>', '', x, flags=re.S)
        x = re.sub(r'<p:bg>.*?</p:bg>', '', x, flags=re.S)
        items = re.findall(r'<p:pic>.*?</p:pic>', x, re.S) + [sp for sp in re.findall(r'<p:sp>.*?</p:sp>', x, re.S) if '<a:blipFill' in sp]
        # identical pictures stacked at the same place look like one: count them once
        sig = lambda i: (tuple(media_hash(part, r) for r in re.findall(r'r:embed="([^"]+)"', i)), tuple(re.findall(r'<a:off [^>]*/><a:ext [^>]*/>', i)))
        return len({sig(i) for i in items if not (template and '<p:ph' in i)})

    def bg_pic(x):
        m = re.search(r'<p:bg>(.*?)</p:bg>', x, re.S)
        return None if not m else ('<a:blipFill' in m.group(1))

    pres = xml('ppt/presentation.xml')
    prels = xml('ppt/_rels/presentation.xml.rels')
    targets = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', prels)) | {a: b for b, a in re.findall(r'Target="([^"]+)"[^>]*Id="([^"]+)"', prels)}
    out = []
    for rid in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres):
        part = posixpath.normpath(posixpath.join('ppt', targets.get(rid, '')))
        sx = xml(part)
        lay = rel(part, 'slideLayout')
        lx = xml(lay) if lay else ''
        mas = rel(lay, 'slideMaster') if lay else None
        mx = xml(mas) if mas else ''
        n = drawn(sx, False, part)
        if 'showMasterSp="0"' not in sx[:600]:
            n += drawn(lx, True, lay)
            if 'showMasterSp="0"' not in lx[:600]:
                n += drawn(mx, True, mas)
        for b in (bg_pic(sx), bg_pic(lx), bg_pic(mx)):
            if b is not None:
                n += int(b)
                break
        out.append(n)
    return out


def pptx_slide_alt_text(pptx: Path) -> list[str]:
    """Picture alt texts (cNvPr descr) per slide: a tagged PDF exports them as text, the slide does not show them."""
    import zipfile
    z = zipfile.ZipFile(pptx)
    pres = z.read('ppt/presentation.xml').decode('utf8', 'ignore')
    prels = z.read('ppt/_rels/presentation.xml.rels').decode('utf8', 'ignore')
    targets = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', prels)) | {a: b for b, a in re.findall(r'Target="([^"]+)"[^>]*Id="([^"]+)"', prels)}
    out = []
    for rid in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres):
        part = 'ppt/' + targets.get(rid, '').lstrip('./')
        try:
            x = z.read(part).decode('utf8', 'ignore')
        except KeyError:
            x = ''
        out.append(' '.join(html.unescape(d) for d in re.findall(r'<p:cNvPr [^>]*descr="([^"]*)"', x)))
    return out


def pptx_slide_text(pptx: Path) -> list[str]:
    """Text each slide shows, read from the package: its shapes (hidden ones excluded), plus the
    SmartArt drawing and chart titles/categories/series names it references."""
    import posixpath
    import zipfile
    z = zipfile.ZipFile(pptx)
    names = set(z.namelist())
    xml = lambda part: z.read(part).decode('utf8', 'ignore') if part in names else ''
    pres, prels = xml('ppt/presentation.xml'), xml('ppt/_rels/presentation.xml.rels')
    targets = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', prels)) | {a: b for b, a in re.findall(r'Target="([^"]+)"[^>]*Id="([^"]+)"', prels)}
    out = []
    for rid in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres):
        part = posixpath.normpath(posixpath.join('ppt', targets.get(rid, '')))
        x = re.sub(r'<mc:Fallback>.*?</mc:Fallback>', '', xml(part), flags=re.S)
        x = re.sub(r'<p:sp>(?:(?!</p:sp>).)*?<p:cNvPr [^>]*hidden="1".*?</p:sp>', '', x, flags=re.S)
        texts = re.findall(r'<a:t>([^<]*)</a:t>', x)
        d, b = posixpath.split(part)
        for t, target in re.findall(r'Type="[^"]*/(diagramDrawing|chart)"[^>]*Target="([^"]+)"', xml(f'{d}/_rels/{b}.rels')):
            sub = xml(posixpath.normpath(posixpath.join(d, target)))
            texts += re.findall(r'<a:t>([^<]*)</a:t>', sub)
            if t == 'chart':
                for cache in re.findall(r'<c:strCache>.*?</c:strCache>', sub, re.S):
                    texts += re.findall(r'<c:v>([^<]*)</c:v>', cache)
        out.append(html.unescape(' '.join(texts)))
    return out


def source_package(src: Path, work: Path) -> Path | None:
    """The deck as a .pptx package: itself, or a LibreOffice conversion of a binary .ppt."""
    if src.suffix.lower() == '.pptx':
        return src
    soffice = shutil.which('soffice') or shutil.which('libreoffice')
    if not soffice:
        return None
    run([soffice, '--headless', '--convert-to', 'pptx', '--outdir', str(work), str(src)], timeout=300)
    conv = work / (src.stem + '.pptx')
    return conv if conv.exists() else None


def corner_colours(png: Path) -> list[tuple[int, int, int]]:
    out = []
    for gravity in ('NorthWest', 'NorthEast', 'SouthWest', 'SouthEast'):
        r = run(['convert', str(png), '-resize', '320x240!', '-gravity', gravity, '-crop', '12x10+0+0', '+repage',
                 '-resize', '1x1!', '-format', '%[fx:int(255*r)],%[fx:int(255*g)],%[fx:int(255*b)]', 'info:'])
        try:
            out.append(tuple(int(v) for v in r.stdout.strip().split(',')))
        except ValueError:
            out.append((0, 0, 0))
    return out


def background_ok(ink: Path, ref: Path) -> tuple[bool, float]:
    a, b = corner_colours(ink), corner_colours(ref)
    d = sorted(sum((x - y) ** 2 for x, y in zip(p, q)) ** .5 for p, q in zip(a, b))
    median = (d[1] + d[2]) / 2
    return median <= 60, round(median, 1)


def check_deck(page, src: Path, work: Path, *, pdf: Path | None = None, expected: list[dict] | None = None) -> dict:
    """Open src in the app and check every slide against a reference PDF or explicit expectations
    ({'text': str, 'images': int} per slide)."""
    page.set_input_files('#fileInput', str(src))
    page.wait_for_function("() => document.querySelectorAll('.slide-thumb').length > 0", timeout=120000)
    page.wait_for_timeout(1500)
    count = page.locator('.slide-thumb').count()
    refs = []
    if pdf:
        run(['pdftoppm', '-r', '48', '-png', str(pdf), str(work / 'ref')])
        refs = sorted(work.glob('ref-*.png'))
    ref_count = len(refs) if pdf else len(expected or [])
    pkg = source_package(src, work) if pdf else None
    images = pptx_slide_images(pkg) if pkg else None
    alts = pptx_slide_alt_text(pkg) if pkg else []
    slides, fails = [], Counter()
    if ref_count and count != ref_count:
        fails['slides'] += 1
    for n in range(1, count + 1):
        thumb = page.locator('.slide-thumb').nth(n - 1)
        sid = thumb.get_attribute('data-slide-id')
        thumb.click()
        page.wait_for_function("(id)=>{const c=document.getElementById('slideCanvas');return !!c&&(!id||c.dataset.slideId===id)}", arg=sid, timeout=20000)
        page.evaluate("()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))")
        page.wait_for_timeout(200)
        got = page.evaluate(PROBE)
        if pdf and n <= len(refs):
            want_text, want_images = pdf_page_text(pdf, n), (images[n - 1] if images and n <= len(images) else 0)
        elif expected and n <= len(expected):
            want_text, want_images = expected[n - 1].get('text', ''), expected[n - 1].get('images', 0)
        else:
            want_text, want_images = '', 0
        missing = missing_words(want_text, got['text'] + '\n' + (alts[n - 1] if n <= len(alts) else ''))
        res = {'slide': n, 'missingWords': missing[:40], 'images': got['images'], 'refImages': want_images,
               'hidden': got['hidden'], 'offslide': got['offslide'], 'authoredHidden': got['authored']}
        res['fail'] = [c for c, bad in (('text', bool(missing)), ('images', got['images'] < want_images),
                                         ('hidden', bool(got['hidden'])), ('offslide', bool(got['offslide']))) if bad]
        if refs and n <= len(refs):
            shot = work / f'ink-{n:03d}.png'
            page.locator('#slideCanvas').first.screenshot(path=str(shot))
            ok, dist = background_ok(shot, refs[n - 1])
            res['backgroundDistance'] = dist
            if not ok:
                res['fail'].append('background')
        for c in res['fail']:
            fails[c] += 1
        slides.append(res)
    return {'file': src.name, 'slides': count, 'refSlides': ref_count, 'reference': 'pdf' if pdf else 'expected',
            'failedSlides': {c: fails[c] for c in CRITERIA}, 'perSlide': slides}


def open_app(pw, chromium: str | None, port: int):
    launch = {'headless': True}
    if chromium and Path(chromium).exists():
        launch['executable_path'] = chromium
    browser = pw.chromium.launch(**launch)
    ctx = browser.new_context(service_workers='block', viewport={'width': 1400, 'height': 900})
    page = ctx.new_page()
    page.goto(f'http://127.0.0.1:{port}/apps/presentations/', wait_until='load')
    page.wait_for_timeout(800)
    return browser, page


def serve():
    port = free_port()
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    return server, port


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+', type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--chromium', default='/opt/pw-browsers/chromium')
    ap.add_argument('--libreoffice', action='store_true', help='without a PDF next to the deck, compare against a LibreOffice render instead of the package itself')
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright
    if not shutil.which('pdftotext'):
        print('pdftotext (poppler-utils) is required', file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    server, port = serve()
    report = []
    try:
        with sync_playwright() as pw:
            for src in args.files:
                src = src.resolve()
                work = args.out / f'{src.stem}-{src.suffix.lstrip(".").lower()}'
                work.mkdir(parents=True, exist_ok=True)
                browser, page = open_app(pw, args.chromium, port)
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)[:200]))
                try:
                    own = src.with_suffix('.pdf')
                    if own.exists() or args.libreoffice:
                        report.append(check_deck(page, src, work, pdf=reference_pdf(src, work)))
                    else:
                        pkg = source_package(src, work)
                        exp = None
                        if pkg:
                            texts, images = pptx_slide_text(pkg), pptx_slide_images(pkg)
                            exp = [{'text': t, 'images': i} for t, i in zip(texts, images)]
                        if not exp:  # the reference cannot read it either (password, damaged): nothing to compare
                            report.append({'file': src.name, 'slides': 0, 'refSlides': 0, 'reference': 'unreadable', 'skipped': True,
                                           'failedSlides': {c: 0 for c in CRITERIA}, 'perSlide': []})
                            print(f'{src.name}: skipped (reference cannot read it)')
                            continue
                        report.append(check_deck(page, src, work, expected=exp))
                except Exception as e:  # the deck did not open or a slide never rendered: everything on it is lost
                    report.append({'file': src.name, 'slides': 0, 'refSlides': 0, 'reference': 'none',
                                   'failedSlides': {'open': 1}, 'error': (errors[-1] if errors else str(e))[:300], 'perSlide': []})
                finally:
                    browser.close()
                r = report[-1]
                bad = ', '.join(f'{c} {n}' for c, n in r['failedSlides'].items() if n) or 'all criteria pass'
                bad += f" ({r['error'][:80]})" if r.get('error') else ''
                print(f"{r['file']}: {r['slides']}/{r['refSlides']} slides - {bad}")
    finally:
        server.terminate()
    (args.out / 'acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return 1 if any(any(r['failedSlides'].values()) for r in report) else 0


if __name__ == '__main__':
    sys.exit(main())
