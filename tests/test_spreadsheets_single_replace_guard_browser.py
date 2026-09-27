#!/usr/bin/env python3
"""Regression: opening another workbook over unsaved changes asks once. The file
input fires both `input` and `change`; the second event must not re-prompt."""
from __future__ import annotations
import io, os, socket, subprocess, sys, tempfile, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8804
BASE=f'http://127.0.0.1:{PORT}'
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'

def fixture(text:str)->bytes:
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml',f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml',f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{NS}"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>{text}</t></is></c></row></sheetData></worksheet>')
    return out.getvalue()

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')

CELL="()=>document.querySelector('#gridStage .cell[data-ref=\"A1\"]')?.innerText"
DIALOG="()=>{const p=document.getElementById('sessionReplacePanel');return !!p&&!p.hidden}"

def main():
    browser_name=os.environ.get('BROWSER','chromium')
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td:
            first=Path(td)/'first.xlsx'; first.write_bytes(fixture('first'))
            second=Path(td)/'second.xlsx'; second.write_bytes(fixture('second'))
            with sync_playwright() as pw:
                args={'headless':True}
                if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
                browser=getattr(pw,browser_name).launch(**args)
                ctx=browser.new_context(viewport={'width':1280,'height':900})
                ctx.add_init_script('window.showOpenFilePicker=undefined')
                page=ctx.new_page()
                page.goto(BASE+'/apps/spreadsheets/',wait_until='load')
                page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1')
                page.set_input_files('#fileInput',str(first))
                page.wait_for_function(f"()=>({CELL})()==='first'")
                page.locator('#gridStage .cell[data-ref="B1"]').click()
                page.keyboard.type('dirty'); page.keyboard.press('Enter')
                page.wait_for_function('() => globalThis.__inkdosSpreadsheetsS1.session.dirty')
                page.click('#menuButton'); page.click('#menuOpen')
                page.wait_for_function(DIALOG)
                with page.expect_file_chooser(timeout=5000) as fc:
                    page.locator('#sessionReplacePanel').get_by_role('button',name='Discard').click()
                fc.value.set_files(str(second))
                page.wait_for_function(f"()=>({CELL})()==='second'")
                page.wait_for_timeout(600)
                assert page.evaluate(DIALOG) is False,'unsaved-changes guard was shown a second time'
                assert page.evaluate('() => globalThis.__inkdosSpreadsheetsS1.session.dirty') is False
                browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Spreadsheets single replace guard ({browser_name}): OK')

if __name__=='__main__':
    main()
