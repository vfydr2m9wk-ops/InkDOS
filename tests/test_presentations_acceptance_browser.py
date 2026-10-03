#!/usr/bin/env python3
"""Level-1 acceptance on synthetic decks: nothing is lost when a deck opens.

The decks are generated into a temporary directory (no fixtures in the repository) from
scripts/presentations_fidelity_corpus.py plus a regression deck for rules fixed against real
PowerPoint output. Expectations come from the generated packages themselves: every word of
every slide is on screen, every picture is drawn, no text is invisible or covered, no text box
leaves the slide. The same checks run on private decks with scripts/presentations_acceptance.py.
"""
from __future__ import annotations

import re
import struct
import sys
import tempfile
import zlib
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import presentations_acceptance as acc  # noqa: E402
import presentations_fidelity_corpus as corpus  # noqa: E402


def png(path: Path, w: int = 24, h: int = 16) -> Path:
    rows = b''.join(b'\x00' + b''.join(bytes((x * 10 % 256, y * 15 % 256, 160)) for x in range(w)) for y in range(h))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
    return path


def raw_text(s: corpus.Slide, x, y, w, h, prst, fill, body, *, wrap='square', anchor='ctr') -> None:
    sid = s._id()
    s.shapes.append(
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="R{sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{corpus.emu(x)}" y="{corpus.emu(y)}"/><a:ext cx="{corpus.emu(w)}" cy="{corpus.emu(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>'
        + (f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>')
        + f'<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="{wrap}" anchor="{anchor}"/><a:lstStyle/>{body}</p:txBody></p:sp>')


def run_xml(t: str, color: str = '000000', size: int = 20) -> str:
    return f'<a:r><a:rPr lang="pt-BR" sz="{size * 100}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr><a:t>{t}</a:t></a:r>'


def regression_deck(tmp: Path) -> list[corpus.Slide]:
    out = []
    s = corpus.Slide()  # symbol-font bullets and percentage spacing
    s.text(36, 10, 648, 40, [corpus.para('Marcadores de símbolo', size=24, algn='ctr')])
    bullets = ''.join(
        f'<a:p><a:pPr marL="342900" indent="-342900"><a:spcBef><a:spcPct val="20000"/></a:spcBef><a:buFont typeface="{f}"/><a:buChar char="{c}"/></a:pPr>{run_xml(t)}</a:p>'
        for f, c, t in (('Wingdings', 'Ø', 'Seta de Wingdings'), ('Wingdings 2', '', 'Círculo de Wingdings dois'), ('Symbol', '', 'Ponto de Symbol')))
    raw_text(s, 60, 80, 600, 200, 'rect', None, bullets, anchor='t')
    out.append(s)
    s = corpus.Slide()  # text inside non-rectangular geometry, arrow connector
    s.text(36, 10, 648, 40, [corpus.para('Formas com texto', size=24, algn='ctr')])
    raw_text(s, 40, 80, 220, 120, 'ellipse', '4F81BD', f'<a:p>{run_xml("Elipse com texto", "FFFFFF")}</a:p>')
    raw_text(s, 320, 80, 300, 150, 'cloudCallout', '4F81BD', f'<a:p>{run_xml("Nuvem com texto branco", "FFFFFF", 18)}</a:p>')
    raw_text(s, 40, 260, 260, 90, 'leftArrowCallout', '339966', f'<a:p>{run_xml("Seta com caixa", "FFFFFF", 16)}</a:p>')
    s.shape(320, 300, 200, 0, 'line', line='800000', tail='triangle')
    out.append(s)
    s = corpus.Slide()  # explicit breaks without wrap, words longer than the box, picture
    s.text(36, 10, 648, 40, [corpus.para('Quebras e palavras longas', size=24, algn='ctr')])
    raw_text(s, 40, 80, 200, 80, 'rect', None,
             f'<a:p>{run_xml("Primeira linha")}<a:br><a:rPr lang="pt-BR" sz="2000"/></a:br>{run_xml("Segunda linha")}</a:p>', wrap='none', anchor='t')
    raw_text(s, 300, 80, 40, 300, 'rect', 'FFFF00', f'<a:p>{run_xml("RESOLUÇÃO", size=14)}</a:p>', anchor='t')
    s.picture(420, 120, 200, 140, str(png(tmp / 'pixel.png')))
    out.append(s)
    return out


def add_sections(pptx: Path) -> None:
    """PowerPoint 2010+ sections repeat every slide id in a p14:sectionLst extension; a deck with sections must still open."""
    import zipfile
    src = zipfile.ZipFile(pptx).read('ppt/presentation.xml').decode('utf-8')
    ids = re.findall(r'<p:sldId id="(\d+)"', src)
    ext = ('<p:extLst><p:ext uri="{521415D9-36F7-43E2-AB2F-B90AF26B5E84}"><p14:sectionLst xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main">'
           '<p14:section name="Seção" id="{11111111-2222-3333-4444-555555555555}"><p14:sldIdLst>' + ''.join(f'<p14:sldId id="{i}"/>' for i in ids)
           + '</p14:sldIdLst></p14:section></p14:sectionLst></p:ext></p:extLst>')
    patched = src.replace('</p:presentation>', ext + '</p:presentation>')
    tmp = pptx.with_suffix('.tmp')
    with zipfile.ZipFile(pptx) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, patched if item.filename == 'ppt/presentation.xml' else zin.read(item.filename))
    tmp.replace(pptx)


def expectations(pptx: Path) -> list[dict]:
    import zipfile
    z = zipfile.ZipFile(pptx)
    images = acc.pptx_slide_images(pptx)
    out = []
    for i in range(1, len(images) + 1):
        x = z.read(f'ppt/slides/slide{i}.xml').decode('utf-8')
        out.append({'text': ' '.join(re.findall(r'<a:t>([^<]*)</a:t>', x)), 'images': images[i - 1]})
    return out


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        decks = [('regression', regression_deck(tmp)), ('corpus-text', corpus.deck_text()), ('corpus-shapes', corpus.deck_shapes())]
        paths = []
        for name, slides in decks:
            p = tmp / f'{name}.pptx'
            corpus.package(slides, p)
            paths.append(p)
        add_sections(paths[0])
        server, port = acc.serve()
        failures = []
        try:
            with sync_playwright() as pw:
                for p in paths:
                    browser, page = acc.open_app(pw, '/opt/pw-browsers/chromium', port)
                    try:
                        work = tmp / p.stem
                        work.mkdir()
                        report = acc.check_deck(page, p, work, expected=expectations(p))
                        if p.stem == 'regression':
                            page.locator('.slide-thumb').nth(0).click()
                            page.wait_for_timeout(300)
                            marks = page.evaluate("()=>[...document.querySelectorAll('#slideCanvas .slide-bullet')].map(b=>b.textContent.trim())")
                            assert marks == ['➢', '●', '•'], marks
                            page.locator('.slide-thumb').nth(2).click()
                            page.wait_for_timeout(300)
                            lines = page.evaluate("""()=>{const p=[...document.querySelectorAll('#slideCanvas .slide-paragraph')].find(x=>x.textContent.includes('Primeira'));
                                const tops=new Set([...p.querySelectorAll('span')].flatMap(s=>[...s.getClientRects()].map(r=>Math.round(r.top))));return tops.size}""")
                            assert lines >= 2, f'explicit line break collapsed in a no-wrap box: {lines}'
                    finally:
                        browser.close()
                    bad = {c: n for c, n in report['failedSlides'].items() if n and c != 'background'}
                    if report['slides'] != report['refSlides'] or bad:
                        failures.append({'file': p.name, 'failed': bad, 'slides': [s for s in report['perSlide'] if s['fail']]})
        finally:
            server.terminate()
        assert not failures, failures
    print('Presentations level-1 acceptance passed on synthetic decks:', ', '.join(p.name for p in paths))


if __name__ == '__main__':
    main()
