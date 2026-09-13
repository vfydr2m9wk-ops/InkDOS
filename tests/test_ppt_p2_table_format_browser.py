#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8792
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1360, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on("console", lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None)
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.p2Tools")
            page.click("#startNew")
            fixture = page.evaluate("""async () => {
                const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                const base=await NS.PptxWriter.build(app.session),zip=await JSZip.loadAsync(base,{checkCRC32:true});
                let slide=await zip.file('ppt/slides/slide1.xml').async('text');
                const table=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="92" name="Format Table"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="1371600"/><a:ext cx="3657600" cy="1371600"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr/><a:tblGrid><a:gridCol w="3657600"/></a:tblGrid><a:tr h="1371600"><a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1600"/><a:t>Cell</a:t></a:r><a:endParaRPr lang="en-US" sz="1600"/></a:p></a:txBody><a:tcPr><a:solidFill><a:srgbClr val="EEEEEE"/></a:solidFill><a:lnL w="12700"><a:solidFill><a:srgbClr val="111111"/></a:solidFill></a:lnL></a:tcPr></a:tc></a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>`;
                slide=slide.replace('</p:spTree>',table+'</p:spTree>');
                zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});
                return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}}));
            }""")
            page.evaluate("""async bytes => {
                const file=new File([new Uint8Array(bytes)],'table-format.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                await globalThis.__inkdosPresentations.open(file);
            }""", fixture)
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.currentSlide?.objects?.some(o => o.type === 'table')")
            changed = page.evaluate("""() => {
                const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                return {
                    fillCommand:app.hasCommand('table.cell.fill.set'),
                    borderCommand:app.hasCommand('table.cell.border.set'),
                    fill:app.executeCommand('table.cell.fill.set',t.id,0,0,'#A1B2C3'),
                    border:app.executeCommand('table.cell.border.set',t.id,0,0,'left','#445566',25400),
                    cell:t.rows[0].cells[0],canUndo:app.history.canUndo
                };
            }""")
            assert changed["fillCommand"] is True, changed
            assert changed["borderCommand"] is True, changed
            assert changed["fill"] is True, changed
            assert changed["border"] is True, changed
            assert changed["cell"]["fill"] == "#A1B2C3", changed
            assert changed["cell"]["borders"]["left"] == {"color": "#445566", "widthEmu": 25400}, changed
            assert changed["canUndo"] is True, changed
            saved = page.evaluate("""async () => {
                const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                const result=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                const xml=await zip.file('ppt/slides/slide1.xml').async('text'),doc=new DOMParser().parseFromString(xml,'application/xml');
                const all=(n,name)=>[...(n?.getElementsByTagName('*')||[])].filter(x=>x.localName===name);
                const frame=all(doc,'graphicFrame').find(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='92'));
                const tc=all(frame,'tc')[0],tcPr=all(tc,'tcPr')[0],solid=[...tcPr.children].find(x=>x.localName==='solidFill'),lnL=[...tcPr.children].find(x=>x.localName==='lnL');
                return {fill:all(solid,'srgbClr')[0]?.getAttribute('val')||'',border:all(lnL,'srgbClr')[0]?.getAttribute('val')||'',width:lnL?.getAttribute('w')||'',receipt:result.receipt};
            }""")
            assert saved["fill"] == "A1B2C3", saved
            assert saved["border"] == "445566", saved
            assert saved["width"] == "25400", saved
            assert saved["receipt"]["modifiedSlideParts"] == ["ppt/slides/slide1.xml"], saved
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
