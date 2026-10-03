#!/usr/bin/env python3
"""Generate a synthetic presentation corpus for fidelity measurement.

Writes hand-built OOXML .pptx files (no third-party packages) that exercise the
features the legacy PPT and PPTX readers must map, then converts each one to a
binary .ppt with LibreOffice when it is installed. Output goes to --out (never
into the repository: corpus files are generated, not fixtures).

    python3 scripts/presentations_fidelity_corpus.py --out /tmp/inkdos-corpus
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

EMU = 12700  # per point
W, H = 9144000, 6858000
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')


def emu(pt: float) -> int:
    return int(pt * EMU)


class Slide:
    def __init__(self) -> None:
        self.shapes: list[str] = []
        self.n = 1

    def _id(self) -> int:
        self.n += 1
        return self.n

    def text(self, x, y, w, h, paragraphs, *, anchor='t', fill=None, line=None, prst='rect', rot=0, wrap='square', autofit=False):
        sid = self._id()
        sp_fill = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>'
        sp_line = f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>' if line else '<a:ln><a:noFill/></a:ln>'
        body = ''.join(paragraphs)
        fit = '<a:spAutoFit/>' if autofit else ''
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="T{sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm rot="{int(rot * 60000)}"><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>{sp_fill}{sp_line}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="{wrap}" anchor="{anchor}">{fit}</a:bodyPr><a:lstStyle/>{body}</p:txBody></p:sp>')

    def shape(self, x, y, w, h, prst, *, fill='4472C4', line='1F3864', rot=0, flip='', dash=None, head=None, tail=None, alpha=None, grad=None):
        sid = self._id()
        if grad:
            fill_xml = ('<a:gradFill><a:gsLst>' + ''.join(f'<a:gs pos="{p}"><a:srgbClr val="{c}"/></a:gs>' for p, c in grad)
                        + '</a:gsLst><a:lin ang="5400000" scaled="1"/></a:gradFill>')
        elif fill:
            a = f'<a:alpha val="{alpha}"/>' if alpha is not None else ''
            fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">{a}</a:srgbClr></a:solidFill>'
        else:
            fill_xml = '<a:noFill/>'
        extra = (f'<a:prstDash val="{dash}"/>' if dash else '') + (f'<a:headEnd type="{head}"/>' if head else '') + (f'<a:tailEnd type="{tail}"/>' if tail else '')
        line_xml = f'<a:ln w="19050"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill>{extra}</a:ln>' if line else '<a:ln><a:noFill/></a:ln>'
        tag = 'p:cxnSp' if prst == 'line' else 'p:sp'
        nv = (f'<p:nvCxnSpPr><p:cNvPr id="{sid}" name="L{sid}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>' if prst == 'line'
              else f'<p:nvSpPr><p:cNvPr id="{sid}" name="S{sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>')
        self.shapes.append(
            f'<{tag}>{nv}<p:spPr><a:xfrm rot="{int(rot * 60000)}"{flip}><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>{fill_xml if prst != "line" else ""}{line_xml}</p:spPr></{tag}>')

    def group(self, x, y, w, h, build):
        sid = self._id()
        inner = Slide()
        inner.n = self.n + 100
        build(inner)
        self.n = inner.n
        self.shapes.append(
            f'<p:grpSp><p:nvGrpSpPr><p:cNvPr id="{sid}" name="G{sid}"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            f'<p:grpSpPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/>'
            f'<a:chOff x="0" y="0"/><a:chExt cx="{emu(w / 2)}" cy="{emu(h / 2)}"/></a:xfrm></p:grpSpPr>'
            + ''.join(inner.shapes) + '</p:grpSp>')

    def xml(self) -> str:
        return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld {NS}><p:cSld><p:spTree>'
                '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
                + ''.join(self.shapes) + '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def para(text, *, size=18, bold=False, italic=False, underline=False, color='000000', font='Arial', algn='l', lvl=0,
         bullet=None, autonum=None, spc_before=0, line_pct=100, runs=None, mar_l=None, indent=None):
    ppr = [f'algn="{algn}"', f'lvl="{lvl}"']
    if mar_l is not None:
        ppr.append(f'marL="{emu(mar_l)}"')
    if indent is not None:
        ppr.append(f'indent="{emu(indent)}"')
    inner = f'<a:lnSpc><a:spcPct val="{line_pct * 1000}"/></a:lnSpc><a:spcBef><a:spcPts val="{spc_before * 100}"/></a:spcBef>'
    if autonum:
        inner += f'<a:buFont typeface="+mj-lt"/><a:buAutoNum type="{autonum}"/>'
    elif bullet:
        inner += f'<a:buFont typeface="Arial"/><a:buChar char="{escape(bullet)}"/>'
    else:
        inner += '<a:buNone/>'

    def run(t, **o):
        b = ' b="1"' if o.get('bold', bold) else ''
        i = ' i="1"' if o.get('italic', italic) else ''
        u = ' u="sng"' if o.get('underline', underline) else ''
        return (f'<a:r><a:rPr lang="pt-BR" sz="{int(o.get("size", size) * 100)}"{b}{i}{u}><a:solidFill><a:srgbClr val="{o.get("color", color)}"/></a:solidFill>'
                f'<a:latin typeface="{o.get("font", font)}"/></a:rPr><a:t>{escape(t)}</a:t></a:r>')

    body = ''.join(run(t, **o) for t, o in runs) if runs else run(text)
    return f'<a:p><a:pPr {" ".join(ppr)}>{inner}</a:pPr>{body}</a:p>'


LOREM = 'A terapia cognitiva propõe que a interpretação dos eventos influencia emoções e comportamentos de maneira consistente.'


def deck_text() -> list[Slide]:
    out = []
    s = Slide()
    s.text(36, 24, 648, 60, [para('Marcadores e níveis', size=32, algn='ctr')], anchor='ctr')
    s.text(54, 100, 612, 400, [
        para('Primeiro nível com marcador', bullet='•', mar_l=27, indent=-27),
        para('Segundo nível', size=16, bullet='–', lvl=1, mar_l=54, indent=-22),
        para('Terceiro nível', size=14, bullet='»', lvl=2, mar_l=81, indent=-20),
        para('Parágrafo sem marcador depois de espaço', spc_before=18),
        para(LOREM, bullet='•', mar_l=27, indent=-27, spc_before=6),
    ])
    out.append(s)
    s = Slide()
    s.text(36, 24, 648, 60, [para('Lista numerada', size=32, algn='ctr')], anchor='ctr')
    s.text(54, 100, 612, 400, [para(f'Item numerado {i}', autonum='arabicPeriod', mar_l=30, indent=-30) for i in range(1, 5)]
           + [para(f'Letra {i}', autonum='alphaLcParenR', lvl=1, mar_l=60, indent=-24, size=16) for i in range(1, 3)])
    out.append(s)
    s = Slide()
    s.text(36, 24, 648, 60, [para('Formatação por trecho', size=32, algn='ctr')], anchor='ctr')
    s.text(54, 110, 612, 140, [para('', runs=[('Normal, ', {}), ('negrito, ', {'bold': True}), ('itálico, ', {'italic': True}),
                                            ('sublinhado, ', {'underline': True}), ('vermelho grande', {'color': 'C00000', 'size': 28})])])
    s.text(54, 260, 300, 200, [para(LOREM, algn='just')], line='808080')
    s.text(370, 260, 300, 200, [para(LOREM, algn='r', line_pct=150)], line='808080')
    out.append(s)
    s = Slide()
    s.text(36, 24, 648, 60, [para('Fontes Office (largura de quebra)', size=28, algn='ctr')], anchor='ctr')
    for i, f in enumerate(['Calibri', 'Cambria', 'Arial', 'Times New Roman', 'Tahoma', 'Century Gothic']):
        s.text(54, 100 + i * 66, 612, 60, [para(f'{f}: ' + LOREM, font=f, size=14)], line='BFBFBF')
    out.append(s)
    s = Slide()
    s.text(36, 24, 648, 60, [para('Tabulações e âncoras', size=28, algn='ctr')], anchor='ctr')
    s.text(54, 100, 612, 40, [para('A\tB\tC\tD')], line='BFBFBF')
    for i, a in enumerate(['t', 'ctr', 'b']):
        s.text(54 + i * 206, 170, 190, 200, [para(f'âncora {a}')], anchor=a, line='808080', fill='F2F2F2')
    s.text(54, 400, 300, 30, [para('Caixa que cresce com o texto ' + LOREM, size=14)], autofit=True, line='808080')
    out.append(s)
    return out


PRESETS = ['rect', 'roundRect', 'ellipse', 'triangle', 'rtTriangle', 'diamond', 'parallelogram', 'trapezoid', 'pentagon', 'hexagon',
           'octagon', 'star5', 'rightArrow', 'leftArrow', 'upArrow', 'downArrow', 'leftRightArrow', 'chevron', 'homePlate', 'plus',
           'cube', 'can', 'lightningBolt', 'heart', 'wedgeRectCallout', 'wedgeEllipseCallout', 'flowChartProcess', 'flowChartDecision',
           'flowChartTerminator', 'leftBrace', 'rightBrace', 'smileyFace']


def deck_shapes() -> list[Slide]:
    out = []
    for chunk in range(0, len(PRESETS), 16):
        s = Slide()
        for i, prst in enumerate(PRESETS[chunk:chunk + 16]):
            x, y = 40 + (i % 4) * 165, 30 + (i // 4) * 125
            s.shape(x, y, 120, 80, prst)
            s.text(x - 10, y + 84, 140, 24, [para(prst, size=10, algn='ctr')])
        out.append(s)
    s = Slide()
    s.text(36, 10, 648, 40, [para('Linhas, setas, rotação, espelho', size=24, algn='ctr')])
    s.shape(60, 80, 200, 120, 'line', line='C00000', tail='triangle')
    s.shape(300, 80, 200, 120, 'line', line='00B050', flip=' flipH="1"', head='arrow', tail='arrow')
    s.shape(560, 60, 0, 160, 'line', line='0070C0', tail='triangle')
    s.shape(80, 260, 160, 60, 'rightArrow', rot=90)
    s.shape(300, 260, 160, 60, 'rightArrow', rot=45)
    s.shape(520, 260, 160, 60, 'rightArrow', rot=180, flip=' flipV="1"')
    s.shape(80, 400, 200, 80, 'rect', fill='FFC000', line='000000', dash='dash')
    s.shape(320, 400, 200, 80, 'roundRect', fill='5B9BD5', alpha=40000)
    s.shape(560, 380, 120, 120, 'rect', fill=None, grad=[(0, 'FFFFFF'), (100000, '1F3864')])
    out.append(s)
    s = Slide()
    s.text(36, 10, 648, 40, [para('Grupo (coordenadas internas)', size=24, algn='ctr')])
    s.group(100, 100, 500, 300, lambda g: (g.shape(0, 0, 100, 60, 'rect', fill='ED7D31'), g.shape(150, 90, 100, 60, 'ellipse', fill='70AD47'),
                                           g.text(0, 100, 120, 40, [para('no grupo', size=14)])))
    out.append(s)
    return out


def package(slides: list[Slide], path: Path) -> None:
    ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
          '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
          '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
          '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>']
    ct += [f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(1, len(slides) + 1)]
    ct.append('</Types>')
    rel = lambda items: ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                         + ''.join(f'<Relationship Id="{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/{t}" Target="{g}"/>' for i, t, g in items) + '</Relationships>')
    theme = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="T"><a:themeElements>'
             '<a:clrScheme name="T"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="44546A"/></a:dk2><a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>'
             + ''.join(f'<a:accent{i}><a:srgbClr val="{c}"/></a:accent{i}>' for i, c in enumerate(['4472C4', 'ED7D31', 'A5A5A5', 'FFC000', '5B9BD5', '70AD47'], 1))
             + '<a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme>'
             '<a:fontScheme name="T"><a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
             '<a:fmtScheme name="T"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
             '<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
             '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
             '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>')
    tree = '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>'
    master = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster {NS}>{tree}'
              '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
              '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>')
    layout = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout {NS} type="blank">{tree}<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'
    pres = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation {NS}><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst>'
            + ''.join(f'<p:sldId id="{256 + i}" r:id="rId{i + 2}"/>' for i in range(len(slides)))
            + f'</p:sldIdLst><p:sldSz cx="{W}" cy="{H}"/><p:notesSz cx="{H}" cy="{W}"/></p:presentation>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ''.join(ct))
        z.writestr('_rels/.rels', rel([('rId1', 'officeDocument', 'ppt/presentation.xml')]))
        z.writestr('ppt/presentation.xml', pres)
        z.writestr('ppt/_rels/presentation.xml.rels', rel([('rId1', 'slideMaster', 'slideMasters/slideMaster1.xml')] + [(f'rId{i + 2}', 'slide', f'slides/slide{i + 1}.xml') for i in range(len(slides))]))
        z.writestr('ppt/slideMasters/slideMaster1.xml', master)
        z.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', rel([('rId1', 'slideLayout', '../slideLayouts/slideLayout1.xml'), ('rId2', 'theme', '../theme/theme1.xml')]))
        z.writestr('ppt/slideLayouts/slideLayout1.xml', layout)
        z.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', rel([('rId1', 'slideMaster', '../slideMasters/slideMaster1.xml')]))
        z.writestr('ppt/theme/theme1.xml', theme)
        for i, s in enumerate(slides, 1):
            z.writestr(f'ppt/slides/slide{i}.xml', s.xml())
            z.writestr(f'ppt/slides/_rels/slide{i}.xml.rels', rel([('rId1', 'slideLayout', '../slideLayouts/slideLayout1.xml')]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--no-ppt', action='store_true', help='skip the LibreOffice .ppt conversion')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    made = []
    for name, build in (('corpus-text', deck_text), ('corpus-shapes', deck_shapes)):
        path = args.out / f'{name}.pptx'
        package(build(), path)
        made.append(path)
    soffice = shutil.which('soffice') or shutil.which('libreoffice')
    if soffice and not args.no_ppt:
        for path in list(made):
            subprocess.run([soffice, '--headless', '--convert-to', 'ppt', '--outdir', str(args.out), str(path)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240, check=False)
            ppt = path.with_suffix('.ppt')
            if ppt.exists():
                made.append(ppt)
    for path in made:
        print(path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
