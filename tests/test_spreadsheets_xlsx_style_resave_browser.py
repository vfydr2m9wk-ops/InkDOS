#!/usr/bin/env python3
"""Regression: a cell style created before the first XLSX save must still exist in
styles.xml on every later save (after a successful, cancelled or failed delivery)."""
from __future__ import annotations
import base64, io, os, re, socket, subprocess, sys, tempfile, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PORT=8797
BASE=f'http://127.0.0.1:{PORT}'
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'

SAVE_STUB=r"""(()=>{window.__saved=[];window.__saveMode='ok';
window.showSaveFilePicker=async(opts)=>{if(window.__saveMode==='abort')throw new DOMException('cancelled','AbortError');
 return {name:(opts&&opts.suggestedName)||'out.xlsx',kind:'file',createWritable:async()=>{if(window.__saveMode==='writefail')throw new DOMException('disk full','QuotaExceededError');const parts=[];
  return {write:async d=>{parts.push(d instanceof Blob?d:new Blob([d]))},close:async()=>{const b=new Uint8Array(await new Blob(parts).arrayBuffer());let s='';for(let i=0;i<b.length;i+=32768)s+=String.fromCharCode.apply(null,b.subarray(i,i+32768));window.__saved.push(btoa(s))}}}}};})();"""

def fixture()->bytes:
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml',f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr('xl/styles.xml',f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="{NS}"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
        z.writestr('xl/worksheets/sheet1.xml',f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{NS}"><sheetData><row r="1"><c r="A1"><v>1</v></c><c r="B1" t="inlineStr"><is><t>Item</t></is></c></row></sheetData></worksheet>')
    return out.getvalue()

def check_styles(data:bytes,label:str)->None:
    z=zipfile.ZipFile(io.BytesIO(data))
    sheet=z.read('xl/worksheets/sheet1.xml').decode()
    styles=z.read('xl/styles.xml').decode()
    count=len(re.findall(r'<xf\b',re.search(r'<cellXfs\b.*?</cellXfs>',styles,re.S).group(0)))
    used=sorted({int(x) for x in re.findall(r'\ss="(\d+)"',sheet)})
    assert used and max(used)<count,{'case':label,'cellXfs':count,'used':used}

def wait_port():
    deadline=time.time()+10
    while time.time()<deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(('127.0.0.1',PORT))==0:return
        time.sleep(.1)
    raise RuntimeError('Local test server did not start')

def run_case(browser,path,first_mode):
    ctx=browser.new_context(viewport={'width':1280,'height':900})
    ctx.add_init_script(SAVE_STUB)
    page=ctx.new_page()
    page.goto(BASE+'/apps/spreadsheets/',wait_until='load')
    page.wait_for_function('() => !!globalThis.__inkdosSpreadsheetsS1')
    page.set_input_files('#fileInput',str(path))
    page.wait_for_function("()=>document.querySelector('#gridStage .cell[data-ref=\"B1\"]')?.innerText==='Item'")
    page.locator('#gridStage .cell[data-ref="A1"]').click()
    page.click('#boldBtn')
    def save(mode):
        page.evaluate(f"()=>{{window.__saveMode='{mode}'}}")
        page.click('#menuButton')
        page.click('#menuSave')
        page.wait_for_timeout(1200)
        for sel in ('#errorClose',):
            if page.locator(sel).is_visible():page.click(sel)
    save(first_mode)
    page.locator('#gridStage .cell[data-ref="C1"]').click()
    page.keyboard.type('later')
    page.keyboard.press('Enter')
    before=page.evaluate('()=>window.__saved.length')
    save('ok')
    page.wait_for_function(f'()=>window.__saved.length>{before}')
    data=base64.b64decode(page.evaluate('()=>window.__saved.at(-1)'))
    ctx.close()
    check_styles(data,first_mode)

def main():
    browser_name=os.environ.get('BROWSER','chromium')
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--bind','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'styles-resave.xlsx'
            path.write_bytes(fixture())
            with sync_playwright() as pw:
                args={'headless':True}
                if os.environ.get('CHROMIUM_PATH') and browser_name=='chromium':args['executable_path']=os.environ['CHROMIUM_PATH']
                browser=getattr(pw,browser_name).launch(**args)
                for first in ('ok','abort','writefail'):
                    run_case(browser,path,first)
                browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
    print(f'Spreadsheets XLSX style re-save regression ({browser_name}): OK')

if __name__=='__main__':
    main()
