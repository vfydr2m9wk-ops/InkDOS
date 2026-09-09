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
PORT = 8794
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local Spreadsheet XLS-S1 test server did not start")


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
            page.goto(BASE + "/apps/spreadsheets/", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1")

            result = page.evaluate(r"""async () => {
                const api=globalThis.__inkdosSpreadsheetsS1, NS=globalThis.InkDOS2Spreadsheets;
                await api.openController.newWorkbook();
                const book=api.session.book, data=book.sheets[0];
                data.name='Data';data.maxR=Math.max(data.maxR,5);data.maxC=Math.max(data.maxC,3);
                const cell=(v,f='')=>({v,f,styleId:0,style:{font:{},border:{}},t:f?'n':(typeof v==='number'?'n':'s'),display:f?'='+f:String(v)});
                data.cells.set('A1',cell(10));data.cells.set('A2',cell(20));data.cells.set('A3',cell(30));
                data.cells.set('B1',cell('', 'SUM(A1:A3)'));
                data.cells.set('C1',cell('', 'LOG10(100)+A2'));
                data.cells.set('D1',cell('', 'IF(A1="A2",A3,0)'));
                const summary=globalThis.LocalXLSX.createBlank().sheets[0];
                summary.name='Summary';summary.maxR=Math.max(summary.maxR,4);summary.maxC=Math.max(summary.maxC,2);
                summary.cells.set('A1',cell('', 'SUM(Data!A1:A3)'));
                summary.cells.set('B1',cell('', 'Data!A2'));
                summary.cells.set('C1',cell('', "SUM('Data'!$A$1:$A$3)"));
                book.sheets.push(summary);book.active=0;
                NS.FormulaEvaluator.recalculate(book);api.editor.render({rebuild:true});

                const formulas=()=>({
                    local:data.cells.get('B1')?.f,
                    functionLike:data.cells.get('C1')?.f,
                    quotedLiteral:data.cells.get('D1')?.f,
                    external:summary.cells.get('A1')?.f,
                    externalSingle:summary.cells.get('B1')?.f,
                    absolute:summary.cells.get('C1')?.f,
                });
                const selection=api.editor.selection, commands=api.editor.commands;
                selection.select(0,0,data,false);
                const inserted=commands.execute('structure.insertRow');
                const afterInsert=formulas();
                commands.execute('edit.undo');
                const afterUndo=formulas();
                commands.execute('edit.redo');
                const afterRedo=formulas();

                selection.select(1,0,data,false);selection.select(2,0,data,true);
                const deleted=commands.execute('structure.deleteRows');
                const afterDelete=formulas();
                commands.execute('edit.undo');
                const afterDeleteUndo=formulas();
                commands.execute('edit.redo');
                const afterDeleteRedo=formulas();

                commands.execute('edit.undo');
                const blob=await globalThis.LocalXLSX.saveCopy(book),bytes=await blob.arrayBuffer();
                const parsed=await globalThis.LocalXLSX.parseWorkbook(bytes,'xls-s1-formulas.xlsx');
                const parsedData=parsed.sheets.find(s=>s.name==='Data'),parsedSummary=parsed.sheets.find(s=>s.name==='Summary');
                return {
                    inserted,deleted,afterInsert,afterUndo,afterRedo,afterDelete,afterDeleteUndo,afterDeleteRedo,
                    roundtrip:{
                        data:parsedData?.cells.get('B1')?.f||'',
                        summary:parsedSummary?.cells.get('A1')?.f||'',
                        single:parsedSummary?.cells.get('B1')?.f||'',
                        absolute:parsedSummary?.cells.get('C1')?.f||'',
                        blobSize:blob.size,
                    },
                    commandOwned:['structure.insertRow','structure.deleteRows','edit.undo','edit.redo'].every(id=>commands.has(id)),
                };
            }""")

            assert result["inserted"] is True, result
            assert result["deleted"] is True, result
            assert result["commandOwned"] is True, result
            assert result["afterInsert"] == {
                "local": "SUM(A1:A4)",
                "functionLike": "LOG10(100)+A3",
                "quotedLiteral": 'IF(A1="A2",A4,0)',
                "external": "SUM(Data!A1:A4)",
                "externalSingle": "Data!A3",
                "absolute": "SUM('Data'!$A$1:$A$4)",
            }, result
            assert result["afterUndo"] == {
                "local": "SUM(A1:A3)",
                "functionLike": "LOG10(100)+A2",
                "quotedLiteral": 'IF(A1="A2",A3,0)',
                "external": "SUM(Data!A1:A3)",
                "externalSingle": "Data!A2",
                "absolute": "SUM('Data'!$A$1:$A$3)",
            }, result
            assert result["afterRedo"] == result["afterInsert"], result
            assert result["afterDelete"] == {
                "local": "SUM(A1:A2)",
                "functionLike": "LOG10(100)+#REF!",
                "quotedLiteral": 'IF(A1="A2",A2,0)',
                "external": "SUM(Data!A1:A2)",
                "externalSingle": "#REF!",
                "absolute": "SUM('Data'!$A$1:$A$2)",
            }, result
            assert result["afterDeleteUndo"] == result["afterInsert"], result
            assert result["afterDeleteRedo"] == result["afterDelete"], result
            assert result["roundtrip"]["data"] == "SUM(A1:A4)", result
            assert result["roundtrip"]["summary"] == "SUM(Data!A1:A4)", result
            assert result["roundtrip"]["single"] == "Data!A3", result
            assert result["roundtrip"]["absolute"] == "SUM('Data'!$A$1:$A$4)", result
            assert result["roundtrip"]["blobSize"] > 500, result
            assert not errors, errors
            browser.close()
        print(f"XLS-S1 structural formulas ({browser_name}): OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
