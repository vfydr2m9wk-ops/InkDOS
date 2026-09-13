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
PORT = 8791
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
                    const cell=(text,fill='')=>`<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1600"/><a:t>${text}</a:t></a:r><a:endParaRPr lang="en-US" sz="1600"/></a:p></a:txBody><a:tcPr>${fill?`<a:solidFill><a:srgbClr val="${fill}"/></a:solidFill>`:''}</a:tcPr></a:tc>`;
                    const table=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="90" name="Merge Table"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="1371600"/><a:ext cx="7315200" cy="2743200"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"><a:tableStyleId>{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}</a:tableStyleId></a:tblPr><a:tblGrid><a:gridCol w="2438400"/><a:gridCol w="2438400"/><a:gridCol w="2438400"/></a:tblGrid><a:tr h="914400">${cell('Leader','EEEEEE')}${cell('')}${cell('Outside 1')}</a:tr><a:tr h="914400">${cell('')}${cell('')}${cell('Outside 2')}</a:tr><a:tr h="914400">${cell('Outside 3')}${cell('Outside 4')}${cell('Outside 5','DDDDDD')}</a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>`;
                    const chart=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="91" name="Chart 1"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="0" y="0"/><a:ext cx="12700" cy="12700"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"/></a:graphic></p:graphicFrame>`;
                    slide=slide.replace('</p:spTree>',table+chart+'</p:spTree>');
                    zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});
                    return Array.from(await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}}));
                }"""
            )
            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'table-merge.pptx',{
                        type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    });
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                fixture,
            )
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide?.objects?.some(o => o.type === 'table')"
            )
            page.wait_for_selector(".slide-table")

            commands = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations;
                    return ['table.cells.merge','table.cells.split'].map(x=>app.hasCommand(x));
                }"""
            )
            assert commands == [True, True], commands

            rejected = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    app.executeCommand('table.cell.text.set',t.id,1,1,'BLOCK');
                    const blocked=app.executeCommand('table.cells.merge',t.id,0,0,1,1);
                    app.executeCommand('history.undo');
                    const current=app.session.currentSlide.objects.find(o=>o.type==='table');
                    return {blocked,text:current.rows[1].cells[1].text};
                }"""
            )
            assert rejected == {"blocked": False, "text": ""}, rejected

            merged = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const result=app.executeCommand('table.cells.merge',t.id,0,0,1,1),current=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const cells=current.rows.map(r=>r.cells.map(c=>({text:c.text,colSpan:c.colSpan,rowSpan:c.rowSpan,hMerge:c.hMerge,vMerge:c.vMerge})));
                    const rowBlocked=app.executeCommand('table.row.insert',current.id,1),columnBlocked=app.executeCommand('table.column.insert',current.id,1);
                    return {result,cells,rowBlocked,columnBlocked,ops:current.pptP2StructureOps||[]};
                }"""
            )
            assert merged["result"] is True, merged
            assert merged["rowBlocked"] is False and merged["columnBlocked"] is False, merged
            assert merged["cells"][0][0] == {"text":"Leader","colSpan":2,"rowSpan":2,"hMerge":False,"vMerge":False}, merged
            assert merged["cells"][0][1]["hMerge"] is True and merged["cells"][0][1]["vMerge"] is False, merged
            assert merged["cells"][1][0]["hMerge"] is False and merged["cells"][1][0]["vMerge"] is True, merged
            assert merged["cells"][1][1]["hMerge"] is True and merged["cells"][1][1]["vMerge"] is True, merged
            assert merged["ops"] == [{"kind":"cells.merge","startRow":0,"startColumn":0,"endRow":1,"endColumn":1}], merged

            rendered = page.evaluate(
                """() => {
                    const cells=[...document.querySelectorAll('.slide-table-cell')],leader=document.querySelector('[data-table-row="0"][data-table-col="0"]');
                    return {count:cells.length,colSpan:leader?.colSpan||0,rowSpan:leader?.rowSpan||0,texts:cells.map(x=>x.textContent)};
                }"""
            )
            assert rendered["count"] == 6, rendered
            assert rendered["colSpan"] == 2 and rendered["rowSpan"] == 2, rendered
            assert rendered["texts"][0] == "Leader", rendered

            history = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations;
                    app.executeCommand('history.undo');
                    const u=app.session.currentSlide.objects.find(o=>o.type==='table'),undo={span:[u.rows[0].cells[0].colSpan,u.rows[0].cells[0].rowSpan],visible:document.querySelectorAll('.slide-table-cell').length};
                    app.executeCommand('history.redo');
                    const r=app.session.currentSlide.objects.find(o=>o.type==='table'),redo={span:[r.rows[0].cells[0].colSpan,r.rows[0].cells[0].rowSpan],visible:document.querySelectorAll('.slide-table-cell').length};
                    return {undo,redo};
                }"""
            )
            assert history["undo"] == {"span":[1,1],"visible":9}, history
            assert history["redo"] == {"span":[2,2],"visible":6}, history

            merged_save = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text'),doc=new DOMParser().parseFromString(xml,'application/xml');
                    const all=(n,name)=>[...(n?.getElementsByTagName('*')||[])].filter(x=>x.localName===name);
                    const frame=all(doc,'graphicFrame').find(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='90')),tbl=all(frame,'tbl')[0],rows=all(tbl,'tr'),cells=rows.map(r=>[...r.children].filter(x=>x.localName==='tc'));
                    const attrs=tc=>({gridSpan:tc.getAttribute('gridSpan'),rowSpan:tc.getAttribute('rowSpan'),hMerge:tc.getAttribute('hMerge'),vMerge:tc.getAttribute('vMerge')});
                    const structure=result.receipt.modifiedObjects.find(x=>x.kind==='table-structure');
                    return {bytes:Array.from(result.bytes),receipt:result.receipt,xml,leader:attrs(cells[0][0]),topRight:attrs(cells[0][1]),bottomLeft:attrs(cells[1][0]),bottomRight:attrs(cells[1][1]),leaderText:all(cells[0][0],'t').map(t=>t.textContent||'').join(''),outside:all(cells[2][2],'t').map(t=>t.textContent||'').join(''),chart:all(doc,'graphicFrame').some(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='91')),style:all(tbl,'tableStyleId')[0]?.textContent||'',operations:structure?.operations||[]};
                }"""
            )
            assert merged_save["leader"] == {"gridSpan":"2","rowSpan":"2","hMerge":None,"vMerge":None}, merged_save
            assert merged_save["topRight"]["hMerge"] == "1" and merged_save["topRight"]["vMerge"] is None, merged_save
            assert merged_save["bottomLeft"]["hMerge"] is None and merged_save["bottomLeft"]["vMerge"] == "1", merged_save
            assert merged_save["bottomRight"]["hMerge"] == "1" and merged_save["bottomRight"]["vMerge"] == "1", merged_save
            assert merged_save["leaderText"] == "Leader" and merged_save["outside"] == "Outside 5", merged_save
            assert merged_save["chart"] is True, merged_save
            assert merged_save["style"] == "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}", merged_save
            assert merged_save["operations"] == [{"kind":"cells.merge","startRow":0,"startColumn":0,"endRow":1,"endColumn":1}], merged_save

            accepted = page.evaluate(
                """async payload => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    app.session.acceptConfirmedPptx(new Uint8Array(payload.bytes),payload.receipt);
                    const t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const clean=await NS.PptxPreservationWriter.build(app.session);
                    return {pending:Object.prototype.hasOwnProperty.call(t,'pptP2StructureOps'),dirty:app.session.dirty,parts:clean.receipt.modifiedSlideParts,objects:clean.receipt.modifiedObjects,structureEditable:app.p2Tools.tableStructureEditable(t.id)};
                }""",
                {"bytes": merged_save["bytes"], "receipt": merged_save["receipt"]},
            )
            assert accepted["pending"] is False and accepted["dirty"] is False, accepted
            assert accepted["parts"] == [] and accepted["objects"] == [], accepted
            assert accepted["structureEditable"] is False, accepted

            split = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const result=app.executeCommand('table.cells.split',t.id,0,0),current=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const flags=current.rows.slice(0,2).map(r=>r.cells.slice(0,2).map(c=>({colSpan:c.colSpan,rowSpan:c.rowSpan,hMerge:c.hMerge,vMerge:c.vMerge,text:c.text})));
                    return {result,flags,structureEditable:app.p2Tools.tableStructureEditable(current.id),ops:current.pptP2StructureOps||[]};
                }"""
            )
            assert split["result"] is True, split
            assert split["structureEditable"] is True, split
            assert split["flags"][0][0]["text"] == "Leader", split
            for row in split["flags"]:
                for cell in row:
                    assert cell["colSpan"] == 1 and cell["rowSpan"] == 1 and cell["hMerge"] is False and cell["vMerge"] is False, split
            assert split["ops"] == [{"kind":"cells.split","row":0,"column":0}], split

            split_save = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text'),doc=new DOMParser().parseFromString(xml,'application/xml');
                    const all=(n,name)=>[...(n?.getElementsByTagName('*')||[])].filter(x=>x.localName===name);
                    const frame=all(doc,'graphicFrame').find(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='90')),tbl=all(frame,'tbl')[0],cells=all(tbl,'tc').slice(0,5),attrs=['gridSpan','rowSpan','hMerge','vMerge'];
                    const structure=result.receipt.modifiedObjects.find(x=>x.kind==='table-structure');
                    return {attrs:cells.map(tc=>Object.fromEntries(attrs.map(a=>[a,tc.getAttribute(a)]))),leaderText:all(cells[0],'t').map(t=>t.textContent||'').join(''),operations:structure?.operations||[]};
                }"""
            )
            for attrs in split_save["attrs"]:
                assert attrs == {"gridSpan":None,"rowSpan":None,"hMerge":None,"vMerge":None}, split_save
            assert split_save["leaderText"] == "Leader", split_save
            assert split_save["operations"] == [{"kind":"cells.split","row":0,"column":0}], split_save

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPT-P2 table merge/split regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
