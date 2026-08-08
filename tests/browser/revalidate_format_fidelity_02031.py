#!/usr/bin/env python3
"""Browser regression for DOCX drawing extents and direct PPTX slide backgrounds."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile
import base64
import json
import re
import sys

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'tests/compatibility-fixtures/documents/era2_office_2007_2013_baseline.docx'
PPT = ROOT / 'tests/compatibility-fixtures/presentations/era2_office_2007_2013_baseline.pptx'
OUT = ROOT / 'tests/browser/results'
OUT.mkdir(parents=True, exist_ok=True)


def clean(page, rel):
    soup = BeautifulSoup((ROOT / rel).read_text(encoding='utf-8'), 'html.parser')
    for node in soup.find_all(['script', 'link']):
        node.decompose()
    if soup.head:
        soup.head.insert(0, soup.new_tag('base', href=ROOT.as_uri() + '/'))
    page.set_content(str(soup), wait_until='domcontentloaded')


def load_documents(page):
    clean(page, 'apps/documents/index.html')
    for rel in ('apps/documents/styles.css', 'shared/office-shell.css', 'shared/ui/visual-foundation-v0203.css', 'shared/ui/content-workspaces-v02031.css', 'shared/ui/workspace-unification-v02031.css'):
        page.add_style_tag(path=str(ROOT / rel))
    for rel in ('shared/office-runtime.js', 'shared/vendor/pako_inflate.min.js', 'apps/documents/drawing-layout.js', 'apps/documents/docx-parser.js', 'shared/vendor/jszip.min.js', 'apps/documents/docx-writer.js', 'shared/ui/workspace-panel-controller.js', 'shared/ui/document-ruler-model.js', 'shared/ui/document-ruler-drag-controller.js', 'shared/ui/workspace-layout.js', 'shared/office-shell.js', 'shared/local-recovery.js', 'apps/documents/app.js'):
        page.add_script_tag(path=str(ROOT / rel))


def load_presentations(page):
    clean(page, 'apps/presentations/index.html')
    for rel in ('apps/presentations/styles.css', 'shared/office-shell.css', 'shared/ui/visual-foundation-v0203.css', 'shared/ui/workspace-unification-v02031.css'):
        page.add_style_tag(path=str(ROOT / rel))
    for rel in ('shared/office-runtime.js', 'shared/vendor/jszip.min.js', 'apps/presentations/engine/compatibility.js', 'apps/presentations/engine/background-resolver.js', 'shared/office-shell.js', 'shared/local-recovery.js', 'apps/presentations/state/selection-controller.js', 'apps/presentations/state/history-controller.js', 'apps/presentations/ui/inspector-controller.js', 'apps/presentations/ui/thumbnails-controller.js', 'apps/presentations/ui/presenter-notes-controller.js', 'apps/presentations/presentation/slideshow-controller.js', 'apps/presentations/io/pptx-write-adapter.js', 'apps/presentations/io/file-controller.js', 'apps/presentations/io/recovery-controller.js', 'apps/presentations/app.js'):
        page.add_script_tag(path=str(ROOT / rel))


def expected_doc_image_width():
    with ZipFile(DOC) as archive:
        xml = archive.read('word/document.xml').decode('utf-8', 'replace')
    match = re.search(r'<wp:extent cx="(\d+)" cy="(\d+)"', xml)
    if not match:
        raise AssertionError('DOCX fixture has no wp:extent')
    return int(match.group(1)) / 9525


def make_direct_background_pptx(destination: Path):
    with ZipFile(PPT) as source, ZipFile(destination, 'w', ZIP_DEFLATED) as output:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == 'ppt/slides/slide1.xml':
                text = data.decode('utf-8')
                bg = '<p:bg><p:bgPr><a:blipFill><a:blip r:embed="rIdBg"/><a:stretch><a:fillRect/></a:stretch></a:blipFill><a:effectLst/></p:bgPr></p:bg>'
                text = text.replace('<p:cSld>', '<p:cSld>' + bg, 1)
                data = text.encode('utf-8')
            elif info.filename == 'ppt/slides/_rels/slide1.xml.rels':
                text = data.decode('utf-8')
                rel = '<Relationship Id="rIdBg" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.png"/>'
                text = text.replace('</Relationships>', rel + '</Relationships>', 1)
                data = text.encode('utf-8')
            output.writestr(info, data)



def make_anchored_letterhead_docx(destination: Path):
    png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+K3s5WQAAAABJRU5ErkJggg==')
    content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
</Types>'''
    package_rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    styles = '''<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults></w:styles>'''
    document = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>
<w:p><w:pPr><w:ind w:left="5100"/></w:pPr><w:r><w:drawing><wp:anchor behindDoc="0"><wp:positionH relativeFrom="column"><wp:posOffset>0</wp:posOffset></wp:positionH><wp:positionV relativeFrom="paragraph"><wp:posOffset>0</wp:posOffset></wp:positionV><wp:extent cx="1905000" cy="762000"/><a:graphic><a:graphicData><pic:pic><pic:blipFill><a:blip r:embed="rIdLogo"/></pic:blipFill></pic:pic></a:graphicData></a:graphic></wp:anchor></w:drawing></w:r><w:r><w:t>Right column text</w:t></w:r></w:p>
<w:p><w:r><w:t>Body text beneath the floating logo.</w:t></w:r></w:p>
<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader"/><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
</w:body></w:document>'''
    document_rels = '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo.png"/><Relationship Id="rIdHeader" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/></Relationships>'''
    header = '''<?xml version="1.0" encoding="UTF-8"?><w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml"><w:p><w:r><w:pict><v:shape style="position:absolute;margin-left:90pt;margin-top:140pt;width:468pt;height:496pt;mso-position-horizontal-relative:margin;mso-position-vertical-relative:margin"><v:imagedata r:id="rIdWatermark"/></v:shape></w:pict></w:r></w:p></w:hdr>'''
    header_rels = '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdWatermark" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/watermark.png"/></Relationships>'''
    with ZipFile(destination, 'w', ZIP_DEFLATED) as output:
        output.writestr('[Content_Types].xml', content_types)
        output.writestr('_rels/.rels', package_rels)
        output.writestr('word/document.xml', document)
        output.writestr('word/styles.xml', styles)
        output.writestr('word/_rels/document.xml.rels', document_rels)
        output.writestr('word/header1.xml', header)
        output.writestr('word/_rels/header1.xml.rels', header_rels)
        output.writestr('word/media/logo.png', png)
        output.writestr('word/media/watermark.png', png)

def main():
    checks = []
    def check(name, passed, details=None):
        checks.append({'name': name, 'passed': bool(passed), 'details': details})
        if not passed:
            raise AssertionError(f'{name}: {details}')

    with TemporaryDirectory() as temp, sync_playwright() as playwright:
        browser = launch_browser(playwright)

        page = browser.new_page(viewport={'width': 1474, 'height': 1024})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        load_documents(page)
        page.set_input_files('#fileInput', str(DOC))
        page.wait_for_function("document.querySelector('#statusText').textContent.includes('opened')", timeout=30000)
        actual_width = page.locator('.page-content img').first.evaluate('e=>e.getBoundingClientRect().width')
        overflows = page.eval_on_selector_all('.page-content', 'els=>els.map(e=>e.scrollHeight-e.clientHeight)')
        check('DOCX drawing uses OOXML extent', abs(actual_width - expected_doc_image_width()) < 1.0, {'actual': actual_width, 'expected': expected_doc_image_width()})
        check('DOCX pages do not clip vertically', all(value <= 3 for value in overflows), overflows)
        check('DOCX no runtime errors', not errors, errors)
        page.close()

        letterhead_path = Path(temp) / 'anchored-letterhead.docx'
        make_anchored_letterhead_docx(letterhead_path)
        page = browser.new_page(viewport={'width': 1474, 'height': 1024})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        load_documents(page)
        page.set_input_files('#fileInput', str(letterhead_path))
        page.wait_for_function("document.querySelector('#statusText').textContent.includes('opened')", timeout=30000)
        state = page.evaluate("""()=>{const content=document.querySelector('.page-content'),image=document.querySelector('.docx-anchored-image'),watermark=document.querySelector('.page-watermark'),paragraph=image&&image.closest('p'),cr=content.getBoundingClientRect(),ir=image.getBoundingClientRect(),wr=watermark.getBoundingClientRect(),pr=document.querySelector('.page').getBoundingClientRect();return{pages:document.querySelectorAll('.page').length,imageLeft:ir.left-cr.left,imageWidth:ir.width,paragraphMargin:parseFloat(getComputedStyle(paragraph).marginLeft),watermarks:document.querySelectorAll('.page-watermark').length,watermarkWidth:wr.width,watermarkLeft:wr.left-pr.left,overflow:content.scrollHeight-content.clientHeight}}""")
        check('DOCX floating image is anchored to the text column instead of paragraph indent', abs(state['imageLeft']) < 1.0, state)
        check('DOCX floating image keeps declared extent', abs(state['imageWidth'] - 200) < 1.0, state)
        check('DOCX indented text remains independently positioned', abs(state['paragraphMargin'] - 340) < 1.0, state)
        check('DOCX VML header watermark is rendered once', state['watermarks'] == 1 and abs(state['watermarkWidth'] - 624) < 1.0, state)
        check('DOCX anchored letterhead does not change pagination flow', state['pages'] == 1 and state['overflow'] <= 3, state)
        check('DOCX anchored letterhead no runtime errors', not errors, errors)
        page.close()

        ppt_path = Path(temp) / 'direct-background.pptx'
        make_direct_background_pptx(ppt_path)
        page = browser.new_page(viewport={'width': 1474, 'height': 1024})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        load_presentations(page)
        page.set_input_files('#fileInput', str(ppt_path))
        page.wait_for_function('window.__LocalPresentationsDebug && window.__LocalPresentationsDebug.getPresentation() && window.__LocalPresentationsDebug.getPresentation().slides.length > 0', timeout=30000)
        state = page.evaluate("""()=>{const s=window.__LocalPresentationsDebug.getPresentation().slides[0],c=document.querySelector('#slideCanvas');return{model:s.backgroundImage||'',rendered:getComputedStyle(c).backgroundImage,size:getComputedStyle(c).backgroundSize}}""")
        check('PPTX direct background image resolved', 'data:image/png;base64,' in state['model'], state['model'][:80])
        check('PPTX direct background image rendered', 'data:image/png;base64,' in state['rendered'], state['rendered'][:80])
        check('PPTX direct background covers full slide coordinates', state['size'] == '100% 100%', state['size'])
        check('PPTX no runtime errors', not errors, errors)
        page.close()
        browser.close()

    result = {'browser': requested_browser_name(), 'checks': checks, 'passed': sum(item['passed'] for item in checks), 'total': len(checks)}
    (OUT / 'format_fidelity_02031.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
