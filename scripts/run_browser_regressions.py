#!/usr/bin/env python3
from pathlib import Path
import argparse, asyncio, base64, re, shutil

ROOT = Path(__file__).resolve().parents[1]


def inline_page(rel):
    page_path = ROOT / rel
    html = page_path.read_text()

    def script(match):
        src = match.group(1).split('?', 1)[0]
        target = (page_path.parent / src).resolve()
        if not target.exists():
            return ''
        return '<script>' + target.read_text() + '</script>'

    html = re.sub(r'''<script\s+src=["']([^"']+)["'][^>]*></script>''', script, html, flags=re.I)

    def style(match):
        target = (page_path.parent / match.group(1).split('?', 1)[0]).resolve()
        return '<style>' + (target.read_text() if target.exists() else '') + '</style>'

    return re.sub(r'''<link[^>]+rel=["']stylesheet["'][^>]+href=["']([^"']+)["'][^>]*>''', style, html, flags=re.I)


def b64(path):
    return base64.b64encode((ROOT / path).read_bytes()).decode()


async def main_async():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        system_browser = (
            shutil.which('chromium') or shutil.which('chromium-browser') or
            shutil.which('google-chrome') or shutil.which('msedge')
        )
        browser = await pw.chromium.launch(
            headless=True,
            executable_path=system_browser,
            args=['--no-sandbox'],
        )

        page = await browser.new_page()
        html = (
            '<!doctype html><body><script>' + (ROOT / 'shared/vendor/pako_inflate.min.js').read_text() + '</script>'
            '<script>' + (ROOT / 'shared/office-runtime.js').read_text() + '</script>'
            '<script>' + (ROOT / 'shared/safe-dom.js').read_text() + '</script>'
            '<script>' + (ROOT / 'apps/documents/docx-parser.js').read_text() + '</script></body>'
        )
        await page.set_content(html)
        for fixture in ('tests/fixtures/inkdesk-letterhead-a4.docx', 'tests/fixtures/inkdesk-letterhead-a4-bom.docx'):
            doc = await page.evaluate(
                '''async b=>{const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);const r=await LocalDocxParser.parse(a.buffer);return{blocks:r.blocks.length,width:r.pageSpec.widthPx,height:r.pageSpec.heightPx,header:r.pageSpec.headerHtml,footer:r.pageSpec.footerHtml,tables:r.blocks.filter(x=>x.type==='table').length};}''',
                b64(fixture),
            )
            assert doc['blocks'] >= 5 and doc['tables'] >= 2 and '<img' in doc['header'] and doc['footer'] and abs(doc['width'] / doc['height'] - 210 / 297) < .02, (fixture, doc)
        await page.close()

        page = await browser.new_page()
        await page.set_content(
            '<!doctype html><body><script>' + (ROOT / 'shared/office-runtime.js').read_text() + '</script>'
            '<script>' + (ROOT / 'apps/spreadsheets/xls-biff8-engine.js').read_text() + '</script></body>'
        )
        xls = await page.evaluate(
            '''async b=>{const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);const r=await LocalXLS.parseWorkbook(a.buffer,'fixture.xls'),sh=r.sheets[0];return{cells:sh.cells.size,borders:[...sh.cells.values()].filter(c=>Object.keys(c.style?.border||{}).length).length,merges:sh.merges.length};}''',
            b64('tests/fixtures/inkdesk-prescription-a4.xls'),
        )
        assert xls['cells'] > 20 and xls['borders'] > 10 and xls['merges'] > 0, xls
        await page.close()

        page = await browser.new_page(viewport={'width': 1200, 'height': 800})
        await page.set_content(inline_page('apps/spreadsheets/index.html'), wait_until='load')
        spreadsheet_start = await page.evaluate(
            """()=>({card:!!document.querySelector('#emptyState .start-card'),newText:document.querySelector('#newEmptyBtn span:last-child')?.textContent.trim(),openText:document.querySelector('#openEmptyBtn span:last-child')?.textContent.trim(),newClass:document.querySelector('#newEmptyBtn')?.className,openClass:document.querySelector('#openEmptyBtn')?.className})"""
        )
        assert spreadsheet_start['card'] and spreadsheet_start['newText'] == 'New Spreadsheet' and spreadsheet_start['openText'] == 'Open Spreadsheet' and 'primary' in spreadsheet_start['newClass'] and 'secondary' in spreadsheet_start['openClass'], spreadsheet_start
        await page.close()

        page = await browser.new_page(viewport={'width': 1400, 'height': 900})
        presentation_errors = []
        page.on('pageerror', lambda error: presentation_errors.append(str(error)))
        await page.set_content(inline_page('apps/presentations/index.html'), wait_until='load')
        await page.evaluate(
            '''async b=>{const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);const f=new File([a],'fixture.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});await window.InkDeskWorkspaceOpenFile(f);}''',
            b64('tests/fixtures/inkdesk-presentation-layout.pptx'),
        )
        await page.wait_for_timeout(900)
        background = await page.locator('#slideCanvas').evaluate("e=>getComputedStyle(e).backgroundImage")
        thumbnails = await page.locator('#slideList .thumb').count()
        assert 'data:image' in background and thumbnails >= 2, (background[:80], thumbnails, presentation_errors)
        await page.locator('#slideList .thumb').nth(1).click()
        await page.wait_for_timeout(300)
        assert await page.locator('#slideCanvas .ppt-table').count() >= 1, presentation_errors
        await page.close()

        page = await browser.new_page(viewport={'width': 1400, 'height': 900})
        pdf_errors = []
        page.on('pageerror', lambda error: pdf_errors.append(str(error)))
        await page.goto((ROOT / 'apps/pdf/index.html').as_uri(), wait_until='load')
        await page.evaluate(
            '''async b=>{const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);await window.InkDeskWorkspaceOpenFile(new File([a],'fixture.pdf',{type:'application/pdf'}));}''',
            b64('tests/fixtures/inkdesk-pdf-sample.pdf'),
        )
        await page.wait_for_timeout(1200)
        pdf = await page.evaluate(
            """()=>({state:InkDeskPdfDebug.getState(),hasSidebar:!!document.querySelector('#pageList .page-item'),hasIndex:!!document.querySelector('#outlineList .outline-item'),tools:[...document.querySelectorAll('.annotation-tool')].map(x=>x.dataset.tool),accept:document.querySelector('#fileInput').accept,zoomValues:[...document.querySelectorAll('#zoomSelect option')].map(x=>x.value)})"""
        )
        assert pdf['state']['pageCount'] == 3 and pdf['state']['renderedCanvases'] <= 5 and pdf['state']['pdfjsVersion'] == '3.11.174', pdf
        assert pdf['hasSidebar'] and pdf['hasIndex'], pdf
        assert {'50', '100', '200', '300', '400'}.issubset(set(pdf['zoomValues'])), pdf
        assert {'select', 'highlight', 'underline', 'marker', 'comment', 'text'}.issubset(set(pdf['tools'])) and '.pdf' in pdf['accept'], pdf
        await page.evaluate("InkDeskPdfDebug.addSyntheticAnnotation('highlight')")
        assert await page.evaluate("InkDeskPdfDebug.getState().annotations") == 1, pdf_errors
        await page.evaluate("InkDeskPdfDebug.goToPage(3)")
        await page.wait_for_timeout(100)
        navigation = await page.evaluate("()=>InkDeskPdfDebug.getState()")
        assert navigation['page'] == 3 and navigation['renderedCanvases'] <= 5, navigation
        await page.evaluate("InkDeskPdfDebug.setZoom('50')")
        assert await page.evaluate("InkDeskPdfDebug.getState().zoom") == '50', pdf_errors
        await page.evaluate("InkDeskPdfDebug.setZoom('400')")
        assert await page.evaluate("InkDeskPdfDebug.getState().zoom") == '400', pdf_errors
        await page.evaluate("InkDeskPdfDebug.toggleFullscreen()")
        await page.wait_for_timeout(80)
        await page.evaluate("InkDeskPdfDebug.exitFullscreen()")
        await page.wait_for_timeout(80)
        fullscreen = await page.evaluate("()=>({immersive:document.body.classList.contains('immersive'),native:!!document.fullscreenElement})")
        assert not fullscreen['immersive'] and not fullscreen['native'], fullscreen

        await page.evaluate(
            '''async b=>{const s=atob(b),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);await window.InkDeskWorkspaceOpenFile(new File([a],'long-fixture.pdf',{type:'application/pdf'}));}''',
            b64('tests/fixtures/inkdesk-pdf-long-4000-pages.pdf'),
        )
        await page.wait_for_timeout(1200)
        long_pdf = await page.evaluate("()=>InkDeskPdfDebug.getState()")
        assert long_pdf['pageCount'] == 4000 and long_pdf['pagePlaceholders'] == 4000, long_pdf
        assert long_pdf['renderedCanvases'] <= 5, long_pdf
        await page.evaluate("InkDeskPdfDebug.goToPage(3500)")
        await page.wait_for_timeout(100)
        long_jump = await page.evaluate("()=>InkDeskPdfDebug.getState()")
        assert long_jump['page'] == 3500 and long_jump['renderedCanvases'] <= 5, long_jump
        assert not pdf_errors, pdf_errors
        await page.close()

        await browser.close()
    print('OK: browser regressions passed for DOCX, XLS, PPTX and PDF, including a synthetic 4,000-page PDF.')
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', default='all')
    parser.parse_args()
    return asyncio.run(main_async())


if __name__ == '__main__':
    raise SystemExit(main())
