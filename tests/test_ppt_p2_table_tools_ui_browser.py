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
PORT = 8795
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
            page.wait_for_selector("#pptP2TableToolsBtn")
            page.click("#startNew")

            fixture = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const base=await NS.PptxWriter.build(app.session),zip=await JSZip.loadAsync(base,{checkCRC32:true});
                    let slide=await zip.file('ppt/slides/slide1.xml').async('text');
                    const cell=text=>`<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1600"/><a:t>${text}</a:t></a:r><a:endParaRPr lang="en-US" sz="1600"/></a:p></a:txBody><a:tcPr/></a:tc>`;
                    const table=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="90" name="Table 1"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="1371600"/><a:ext cx="7315200" cy="2743200"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"><a:tableStyleId>{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}</a:tableStyleId></a:tblPr><a:tblGrid><a:gridCol w="3657600"/><a:gridCol w="3657600"/></a:tblGrid><a:tr h="1371600">${cell('A')}${cell('B')}</a:tr><a:tr h="1371600">${cell('C')}${cell('D')}</a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>`;
                    slide=slide.replace('</p:spTree>',table+'</p:spTree>');
                    zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});
                    return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}}));
                }"""
            )
            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'table-tools-ui.pptx',{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                fixture,
            )
            page.wait_for_selector(".slide-table")
            page.click('[data-table-row="0"][data-table-col="0"]')
            page.wait_for_function("() => !document.getElementById('pptP2TableToolsBtn').disabled")
            page.click("#pptP2TableToolsBtn")
            assert page.locator("#pptP2TableToolsPanel").is_visible()
            meta = page.locator("#pptP2TableMeta").inner_text()
            assert "Cell 1, 1" in meta, meta

            page.evaluate("""() => {const input=document.getElementById('pptP2TableFill');input.value='#112233';input.dispatchEvent(new Event('change',{bubbles:true}))}""")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.currentSlide.objects.find(o=>o.type==='table').rows[0].cells[0].fill === '#112233'")
            page.click("#pptP2InsertRow")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.currentSlide.objects.find(o=>o.type==='table').rows.length === 3")
            page.evaluate("() => globalThis.__inkdosPresentations.executeCommand('history.undo')")
            page.wait_for_function("() => globalThis.__inkdosPresentations.session.currentSlide.objects.find(o=>o.type==='table').rows.length === 2")

            state = page.evaluate("""() => ({panel:!document.getElementById('pptP2TableToolsPanel').hidden,commands:globalThis.__inkdosPresentations.listCommands().filter(x=>x.startsWith('table.')).sort()})""")
            assert state["panel"] is True, state
            assert "table.cell.fill.set" in state["commands"], state
            assert "table.row.insert" in state["commands"], state
            browser.close()
        assert not errors, errors
        print(f"PPT-P2 Table Tools UI browser regression passed ({browser_name}).")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
