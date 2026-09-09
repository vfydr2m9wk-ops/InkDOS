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
PORT = 8793
BASE = f"http://127.0.0.1:{PORT}"
OLD_STYLE = "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"
NEW_STYLE = "{5940675A-B579-460E-94D1-54222C63F5DA}"


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
            fixture = page.evaluate("""async oldStyle => {
                const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                const base=await NS.PptxWriter.build(app.session),zip=await JSZip.loadAsync(base,{checkCRC32:true});
                let slide=await zip.file('ppt/slides/slide1.xml').async('text');
                const table=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="93" name="Style Table"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="1371600"/><a:ext cx="3657600" cy="1371600"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1" bandRow="1"><a:tableStyleId>${oldStyle}</a:tableStyleId></a:tblPr><a:tblGrid><a:gridCol w="3657600"/></a:tblGrid><a:tr h="1371600"><a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1600"/><a:t>Styled cell</a:t></a:r><a:endParaRPr lang="en-US" sz="1600"/></a:p></a:txBody><a:tcPr/></a:tc></a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>`;
                slide=slide.replace('</p:spTree>',table+'</p:spTree>');
                zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});
                return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}}));
            }""", OLD_STYLE)
            page.evaluate("""async bytes => {
                const file=new File([new Uint8Array(bytes)],'table-style.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                await globalThis.__inkdosPresentations.open(file);
            }""", fixture)
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.currentSlide?.objects?.some(o => o.type === 'table')")

            changed = page.evaluate("""newStyle => {
                const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                const before=t.styleId;
                const invalid=app.executeCommand('table.style.set',t.id,'not-a-guid');
                const applied=app.executeCommand('table.style.set',t.id,newStyle.toLowerCase());
                return {command:app.hasCommand('table.style.set'),before,invalid,applied,after:t.styleId,canUndo:app.history.canUndo};
            }""", NEW_STYLE)
            assert changed["command"] is True, changed
            assert changed["before"] == OLD_STYLE, changed
            assert changed["invalid"] is False, changed
            assert changed["applied"] is True, changed
            assert changed["after"] == NEW_STYLE, changed
            assert changed["canUndo"] is True, changed

            undo_style = page.evaluate("""() => {const app=globalThis.__inkdosPresentations;app.executeCommand('history.undo');return app.session.currentSlide.objects.find(o=>o.type==='table').styleId}""")
            assert undo_style == OLD_STYLE, undo_style
            redo_style = page.evaluate("""() => {const app=globalThis.__inkdosPresentations;app.executeCommand('history.redo');return app.session.currentSlide.objects.find(o=>o.type==='table').styleId}""")
            assert redo_style == NEW_STYLE, redo_style

            saved = page.evaluate("""async () => {
                const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                const result=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                const xml=await zip.file('ppt/slides/slide1.xml').async('text'),doc=new DOMParser().parseFromString(xml,'application/xml');
                const all=(n,name)=>[...(n?.getElementsByTagName('*')||[])].filter(x=>x.localName===name);
                const frame=all(doc,'graphicFrame').find(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='93'));
                const tbl=all(frame,'tbl')[0],tblPr=all(tbl,'tblPr')[0],styles=all(tblPr,'tableStyleId');
                return {bytes:Array.from(result.bytes),style:styles[0]?.textContent||'',styleCount:styles.length,firstRow:tblPr?.getAttribute('firstRow'),bandRow:tblPr?.getAttribute('bandRow'),text:all(tbl,'t').map(n=>n.textContent||'').join(''),receipt:result.receipt};
            }""")
            assert saved["style"] == NEW_STYLE, saved
            assert saved["styleCount"] == 1, saved
            assert saved["firstRow"] == "1", saved
            assert saved["bandRow"] == "1", saved
            assert saved["text"] == "Styled cell", saved
            assert saved["receipt"]["modifiedSlideParts"] == ["ppt/slides/slide1.xml"], saved
            assert saved["receipt"]["modifiedObjects"][0]["operations"][0]["kind"] == "table.style", saved

            reopened = page.evaluate("""async bytes => {
                const app=globalThis.__inkdosPresentations;
                const file=new File([new Uint8Array(bytes)],'table-style-roundtrip.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                await app.open(file);
                return app.session.currentSlide.objects.find(o=>o.type==='table')?.styleId||'';
            }""", saved["bytes"])
            assert reopened == NEW_STYLE, reopened
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
