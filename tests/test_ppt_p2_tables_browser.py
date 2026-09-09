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
PORT = 8789
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
            page.on(
                "console",
                lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None,
            )
            page.goto(BASE + "/apps/presentations/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosPresentations?.p2Tools")
            page.click("#startNew")
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.active && "
                "!!globalThis.InkDOS2Presentations?.PptxWriter && !!globalThis.JSZip"
            )

            fixture = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const base=await NS.PptxWriter.build(app.session);
                    const zip=await JSZip.loadAsync(base,{checkCRC32:true});
                    let slide=await zip.file('ppt/slides/slide1.xml').async('text');
                    const table=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="90" name="Table 1"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="1371600"/><a:ext cx="7315200" cy="2743200"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"><a:tableStyleId>{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}</a:tableStyleId></a:tblPr><a:tblGrid><a:gridCol w="3657600"/><a:gridCol w="3657600"/></a:tblGrid><a:tr h="1371600"><a:tc gridSpan="2"><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="ctr"/><a:r><a:rPr lang="en-US" sz="1800" b="1"><a:solidFill><a:schemeClr val="accent2"/></a:solidFill><a:latin typeface="+mj-lt"/></a:rPr><a:t>Merged header</a:t></a:r><a:endParaRPr lang="en-US" sz="1800"/></a:p></a:txBody><a:tcPr marL="91440" marR="91440" marT="45720" marB="45720" anchor="ctr"><a:solidFill><a:schemeClr val="accent1"/></a:solidFill><a:lnL w="25400"><a:solidFill><a:srgbClr val="445566"/></a:solidFill></a:lnL><a:lnR w="25400"><a:solidFill><a:srgbClr val="445566"/></a:solidFill></a:lnR><a:lnT w="25400"><a:solidFill><a:srgbClr val="445566"/></a:solidFill></a:lnT><a:lnB w="25400"><a:solidFill><a:srgbClr val="445566"/></a:solidFill></a:lnB></a:tcPr></a:tc><a:tc hMerge="1"><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US" sz="1800"/></a:p></a:txBody><a:tcPr/></a:tc></a:tr><a:tr h="1371600"><a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1600"/><a:t>Left</a:t></a:r><a:endParaRPr lang="en-US" sz="1600"/></a:p></a:txBody><a:tcPr><a:solidFill><a:srgbClr val="EEEEEE"/></a:solidFill></a:tcPr></a:tc><a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="r"/><a:r><a:rPr lang="en-US" sz="1600" i="1"/><a:t>Right</a:t></a:r><a:endParaRPr lang="en-US" sz="1600"/></a:p></a:txBody><a:tcPr/></a:tc></a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>`;
                    const chart=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="91" name="Chart 1"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="0" y="0"/><a:ext cx="12700" cy="12700"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"/></a:graphic></p:graphicFrame>`;
                    slide=slide.replace('</p:spTree>',table+chart+'</p:spTree>');
                    zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});
                    const out=await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}});
                    return {bytes:Array.from(out),slideXml:slide};
                }"""
            )

            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'table-foundation.pptx',{
                        type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    });
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                fixture["bytes"],
            )
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide?.objects?.some(o => o.type === 'table')"
            )
            page.wait_for_selector(".slide-table")

            imported = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations;
                    const tables=app.session.currentSlide.objects.filter(o=>o.type==='table');
                    const t=tables[0];
                    const fallback=app.session.compatibility.filter(x=>x.includes('table/chart/SmartArt'));
                    return {count:tables.length,table:t,fallback,hasCellCommand:app.hasCommand('table.cell.text.set')};
                }"""
            )
            assert imported["count"] == 1, imported
            assert imported["hasCellCommand"] is True, imported
            table = imported["table"]
            assert [table["x"], table["y"], table["w"], table["h"]] == [914400, 1371600, 7315200, 2743200], table
            assert table["columns"] == [3657600, 3657600], table
            assert [r["heightEmu"] for r in table["rows"]] == [1371600, 1371600], table
            assert table["styleId"] == "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}", table
            assert table["sourceRef"] == {
                "slidePart": "ppt/slides/slide1.xml",
                "shapeId": "90",
                "kind": "table",
            }, table
            assert table["importedUnmapped"] is True, table
            assert table["pptP2Imported"] is True, table
            assert table["rows"][0]["cells"][0]["text"] == "Merged header", table
            assert table["rows"][0]["cells"][0]["colSpan"] == 2, table
            assert table["rows"][0]["cells"][1]["hMerge"] is True, table
            assert table["rows"][0]["cells"][0]["fill"] == "#DF542C", table
            assert table["rows"][0]["cells"][0]["borders"]["left"] == {
                "color": "#445566",
                "widthEmu": 25400,
            }, table
            header_run = table["rows"][0]["cells"][0]["paragraphs"][0]["runs"][0]
            assert header_run["fontFamily"] == "Aptos Display", header_run
            assert header_run["color"] == "#4F81BD", header_run
            assert table["rows"][1]["cells"][1]["paragraphs"][0]["align"] == "right", table
            assert len(imported["fallback"]) == 1, imported

            rendered = page.evaluate(
                """() => {
                    const el=document.querySelector('.slide-table'),cells=[...el.querySelectorAll('.slide-table-cell')],merged=el.querySelector('[data-table-row="0"][data-table-col="0"]'),cols=[...el.querySelectorAll('col')],rows=[...el.querySelectorAll('tr')];
                    return {
                        left:el.style.left,top:el.style.top,width:el.style.width,height:el.style.height,
                        cellCount:cells.length,texts:cells.map(x=>x.textContent),colSpan:merged?.colSpan||0,
                        editable:cells.map(x=>x.querySelector('.table-cell-content')?.contentEditable),
                        background:merged?.style.background||'',borderLeft:merged?.style.borderLeft||'',
                        colWidths:cols.map(x=>x.style.width),rowHeights:rows.map(x=>x.style.height)
                    };
                }"""
            )
            assert rendered["left"] == "72px", rendered
            assert rendered["top"] == "108px", rendered
            assert rendered["width"] == "576px", rendered
            assert rendered["height"] == "216px", rendered
            assert rendered["cellCount"] == 3, rendered
            assert rendered["texts"] == ["Merged header", "Left", "Right"], rendered
            assert rendered["colSpan"] == 2, rendered
            assert rendered["editable"] == ["true", "true", "true"], rendered
            assert rendered["background"], rendered
            assert "2px" in rendered["borderLeft"], rendered
            assert rendered["colWidths"] == ["50%", "50%"], rendered
            assert rendered["rowHeights"] == ["50%", "50%"], rendered

            preserved = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session);
                    const zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text');
                    return {xml,receipt:result.receipt};
                }"""
            )
            assert preserved["xml"] == fixture["slideXml"], preserved["receipt"]
            assert preserved["receipt"]["modifiedSlideParts"] == [], preserved["receipt"]
            assert preserved["receipt"]["modifiedObjects"] == [], preserved["receipt"]

            command_edit = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const blocked=app.executeCommand('table.cell.text.set',t.id,0,1,'must-not-write');
                    const changed=app.executeCommand('table.cell.text.set',t.id,1,0,'Left edited');
                    return {id:t.id,blocked,changed,text:t.rows[1].cells[0].text,canUndo:app.history.canUndo};
                }"""
            )
            assert command_edit["blocked"] is False, command_edit
            assert command_edit["changed"] is True, command_edit
            assert command_edit["text"] == "Left edited", command_edit
            assert command_edit["canUndo"] is True, command_edit

            undo_text = page.evaluate(
                """() => {const app=globalThis.__inkdosPresentations;app.executeCommand('history.undo');return app.session.currentSlide.objects.find(o=>o.type==='table').rows[1].cells[0].text}"""
            )
            assert undo_text == "Left", undo_text
            redo_text = page.evaluate(
                """() => {const app=globalThis.__inkdosPresentations;app.executeCommand('history.redo');return app.session.currentSlide.objects.find(o=>o.type==='table').rows[1].cells[0].text}"""
            )
            assert redo_text == "Left edited", redo_text

            page.evaluate(
                """() => {
                    const content=document.querySelector('[data-table-row="1"][data-table-col="1"] .table-cell-content');
                    content.focus();content.innerText='Right edited';content.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText'}));content.blur();
                }"""
            )
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide.objects.find(o=>o.type==='table').rows[1].cells[1].text === 'Right edited'"
            )

            saved = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text'),doc=new DOMParser().parseFromString(xml,'application/xml');
                    const all=(n,name)=>[...(n?.getElementsByTagName('*')||[])].filter(x=>x.localName===name),child=(n,name)=>[...(n?.children||[])].find(x=>x.localName===name)||null;
                    const frame=all(doc,'graphicFrame').find(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='90')),tbl=all(frame,'tbl')[0],rows=all(tbl,'tr');
                    const texts=rows.map(r=>[...r.children].filter(x=>x.localName==='tc').map(tc=>all(tc,'t').map(t=>t.textContent||'').join('')));
                    const right=[...rows[1].children].filter(x=>x.localName==='tc')[1],rightRPr=all(right,'rPr')[0];
                    const chart=all(doc,'graphicFrame').some(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='91'));
                    return {xml,texts,rightItalic:rightRPr?.getAttribute('i')||null,chart,receipt:result.receipt,grid:all(tbl,'gridCol').map(n=>n.getAttribute('w')),style:all(tbl,'tableStyleId')[0]?.textContent||''};
                }"""
            )
            assert saved["texts"] == [["Merged header", ""], ["Left edited", "Right edited"]], saved
            assert saved["rightItalic"] == "1", saved
            assert saved["chart"] is True, saved
            assert saved["grid"] == ["3657600", "3657600"], saved
            assert saved["style"] == "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}", saved
            assert saved["receipt"]["modifiedSlideParts"] == ["ppt/slides/slide1.xml"], saved["receipt"]
            cell_receipts = [x for x in saved["receipt"]["modifiedObjects"] if x["kind"] == "existing-table-cell"]
            assert [(x["row"], x["column"]) for x in cell_receipts] == [(1, 0), (1, 1)], cell_receipts

            blocked_structure = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table'),before=t.columns[0];
                    t.columns[0]=before+12700;
                    try{await NS.PptxPreservationWriter.build(app.session);return null}catch(e){return String(e?.message||e)}finally{t.columns[0]=before}
                }"""
            )
            assert blocked_structure and "table structure or formatting changed" in blocked_structure, blocked_structure

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPT-P2 tables import/render + cell text regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
