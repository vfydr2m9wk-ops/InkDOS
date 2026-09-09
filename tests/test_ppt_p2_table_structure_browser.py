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
PORT = 8790
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
                    const table=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="90" name="Structure Table"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="1371600"/><a:ext cx="7315200" cy="2743200"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"><a:tableStyleId>{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}</a:tableStyleId></a:tblPr><a:tblGrid><a:gridCol w="3657600"/><a:gridCol w="3657600"/></a:tblGrid><a:tr h="1371600">${cell('A','EEEEEE')}${cell('B')}</a:tr><a:tr h="1371600">${cell('C')}${cell('D','DDDDDD')}</a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>`;
                    const chart=`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="91" name="Chart 1"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="0" y="0"/><a:ext cx="12700" cy="12700"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart"/></a:graphic></p:graphicFrame>`;
                    slide=slide.replace('</p:spTree>',table+chart+'</p:spTree>');
                    zip.file('ppt/slides/slide1.xml',slide,{createFolders:false});
                    const out=await zip.generateAsync({type:'uint8array',compression:'DEFLATE',compressionOptions:{level:6}});
                    return Array.from(out);
                }"""
            )
            page.evaluate(
                """async bytes => {
                    const file=new File([new Uint8Array(bytes)],'table-structure.pptx',{
                        type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    });
                    await globalThis.__inkdosPresentations.open(file);
                }""",
                fixture,
            )
            page.wait_for_function(
                "() => globalThis.__inkdosPresentations.session.currentSlide?.objects?.some(o => o.type === 'table')"
            )

            initial = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    return {
                        id:t.id,columns:t.columns,rowHeights:t.rows.map(r=>r.heightEmu),
                        texts:t.rows.map(r=>r.cells.map(c=>c.text)),editable:app.p2Tools.tableStructureEditable(t.id),
                        commands:['table.row.insert','table.row.delete','table.column.insert','table.column.delete'].map(x=>app.hasCommand(x))
                    };
                }"""
            )
            assert initial["commands"] == [True, True, True, True], initial
            assert initial["editable"] is True, initial
            assert initial["columns"] == [3657600, 3657600], initial
            assert initial["rowHeights"] == [1371600, 1371600], initial
            assert initial["texts"] == [["A", "B"], ["C", "D"]], initial

            inserted = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const row=app.executeCommand('table.row.insert',t.id,1);
                    const afterRow={rows:t.rows.length,heights:t.rows.map(r=>r.heightEmu),ops:(t.pptP2StructureOps||[]).slice()};
                    app.executeCommand('history.undo');
                    const undoRows=app.session.currentSlide.objects.find(o=>o.type==='table').rows.length;
                    app.executeCommand('history.redo');
                    const rt=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const redoRows=rt.rows.length;
                    const column=app.executeCommand('table.column.insert',rt.id,1);
                    const current=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const text=app.executeCommand('table.cell.text.set',current.id,1,1,'Center');
                    return {row,column,text,afterRow,undoRows,redoRows,columns:current.columns,heights:current.rows.map(r=>r.heightEmu),texts:current.rows.map(r=>r.cells.map(c=>c.text)),ops:current.pptP2StructureOps||[]};
                }"""
            )
            assert inserted["row"] is True and inserted["column"] is True and inserted["text"] is True, inserted
            assert inserted["afterRow"]["rows"] == 3, inserted
            assert inserted["afterRow"]["heights"] == [685800, 685800, 1371600], inserted
            assert inserted["undoRows"] == 2 and inserted["redoRows"] == 3, inserted
            assert inserted["columns"] == [1828800, 1828800, 3657600], inserted
            assert inserted["heights"] == [685800, 685800, 1371600], inserted
            assert inserted["texts"] == [["A", "", "B"], ["", "Center", ""], ["C", "", "D"]], inserted
            assert inserted["ops"] == [
                {"kind": "row.insert", "index": 1},
                {"kind": "column.insert", "index": 1},
            ], inserted

            inserted_save = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text'),doc=new DOMParser().parseFromString(xml,'application/xml');
                    const all=(n,name)=>[...(n?.getElementsByTagName('*')||[])].filter(x=>x.localName===name);
                    const frame=all(doc,'graphicFrame').find(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='90')),tbl=all(frame,'tbl')[0],rows=all(tbl,'tr');
                    const texts=rows.map(r=>[...r.children].filter(x=>x.localName==='tc').map(tc=>all(tc,'t').map(t=>t.textContent||'').join('')));
                    const structure=result.receipt.modifiedObjects.find(x=>x.kind==='table-structure');
                    const cell=result.receipt.modifiedObjects.find(x=>x.kind==='existing-table-cell');
                    const chart=all(doc,'graphicFrame').some(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='91'));
                    return {bytes:Array.from(result.bytes),receipt:result.receipt,xml,texts,grid:all(tbl,'gridCol').map(n=>Number(n.getAttribute('w'))),heights:rows.map(n=>Number(n.getAttribute('h'))),structure,cell,chart,style:all(tbl,'tableStyleId')[0]?.textContent||''};
                }"""
            )
            assert inserted_save["grid"] == [1828800, 1828800, 3657600], inserted_save
            assert inserted_save["heights"] == [685800, 685800, 1371600], inserted_save
            assert inserted_save["texts"] == [["A", "", "B"], ["", "Center", ""], ["C", "", "D"]], inserted_save
            assert inserted_save["structure"]["operations"] == [
                {"kind": "row.insert", "index": 1},
                {"kind": "column.insert", "index": 1},
            ], inserted_save
            assert (inserted_save["cell"]["row"], inserted_save["cell"]["column"]) == (1, 1), inserted_save
            assert inserted_save["chart"] is True, inserted_save
            assert inserted_save["style"] == "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}", inserted_save

            accepted = page.evaluate(
                """async payload => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    app.session.acceptConfirmedPptx(new Uint8Array(payload.bytes),payload.receipt);
                    const t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const clean=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(clean.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text');
                    return {pending:Object.prototype.hasOwnProperty.call(t,'pptP2StructureOps'),dirty:app.session.dirty,parts:clean.receipt.modifiedSlideParts,objects:clean.receipt.modifiedObjects,xml};
                }""",
                {"bytes": inserted_save["bytes"], "receipt": inserted_save["receipt"]},
            )
            assert accepted["pending"] is False, accepted
            assert accepted["dirty"] is False, accepted
            assert accepted["parts"] == [], accepted
            assert accepted["objects"] == [], accepted
            assert accepted["xml"] == inserted_save["xml"], accepted

            deleted = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table');
                    const row=app.executeCommand('table.row.delete',t.id,1);
                    const column=app.executeCommand('table.column.delete',t.id,1);
                    const after=app.session.currentSlide.objects.find(o=>o.type==='table');
                    app.executeCommand('history.undo');
                    const undoCols=app.session.currentSlide.objects.find(o=>o.type==='table').columns.length;
                    app.executeCommand('history.redo');
                    const current=app.session.currentSlide.objects.find(o=>o.type==='table');
                    return {row,column,undoCols,columns:current.columns,heights:current.rows.map(r=>r.heightEmu),texts:current.rows.map(r=>r.cells.map(c=>c.text)),ops:current.pptP2StructureOps||[]};
                }"""
            )
            assert deleted["row"] is True and deleted["column"] is True, deleted
            assert deleted["undoCols"] == 3, deleted
            assert deleted["columns"] == [3657600, 3657600], deleted
            assert deleted["heights"] == [1371600, 1371600], deleted
            assert deleted["texts"] == [["A", "B"], ["C", "D"]], deleted
            assert deleted["ops"] == [
                {"kind": "row.delete", "index": 1},
                {"kind": "column.delete", "index": 1},
            ], deleted

            deleted_save = page.evaluate(
                """async () => {
                    const NS=globalThis.InkDOS2Presentations,app=globalThis.__inkdosPresentations;
                    const result=await NS.PptxPreservationWriter.build(app.session),zip=await JSZip.loadAsync(result.bytes,{checkCRC32:true});
                    const xml=await zip.file('ppt/slides/slide1.xml').async('text'),doc=new DOMParser().parseFromString(xml,'application/xml');
                    const all=(n,name)=>[...(n?.getElementsByTagName('*')||[])].filter(x=>x.localName===name);
                    const frame=all(doc,'graphicFrame').find(f=>all(f,'cNvPr').some(n=>n.getAttribute('id')==='90')),tbl=all(frame,'tbl')[0],rows=all(tbl,'tr');
                    const structure=result.receipt.modifiedObjects.find(x=>x.kind==='table-structure');
                    return {grid:all(tbl,'gridCol').map(n=>Number(n.getAttribute('w'))),heights:rows.map(n=>Number(n.getAttribute('h'))),texts:rows.map(r=>[...r.children].filter(x=>x.localName==='tc').map(tc=>all(tc,'t').map(t=>t.textContent||'').join(''))),operations:structure?.operations||[]};
                }"""
            )
            assert deleted_save["grid"] == [3657600, 3657600], deleted_save
            assert deleted_save["heights"] == [1371600, 1371600], deleted_save
            assert deleted_save["texts"] == [["A", "B"], ["C", "D"]], deleted_save
            assert deleted_save["operations"] == [
                {"kind": "row.delete", "index": 1},
                {"kind": "column.delete", "index": 1},
            ], deleted_save

            merge_block = page.evaluate(
                """() => {
                    const app=globalThis.__inkdosPresentations,t=app.session.currentSlide.objects.find(o=>o.type==='table'),cell=t.rows[0].cells[0];
                    cell.colSpan=2;
                    const editable=app.p2Tools.tableStructureEditable(t.id),result=app.executeCommand('table.row.insert',t.id,1);
                    cell.colSpan=1;
                    return {editable,result};
                }"""
            )
            assert merge_block == {"editable": False, "result": False}, merge_block

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(f"PPT-P2 table row/column structure regression passed on {browser_name}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
