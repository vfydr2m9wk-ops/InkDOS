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
    raise RuntimeError("Local Spreadsheet XLS-S1 column test server did not start")


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
                data.name='Data';data.maxR=Math.max(data.maxR,5);data.maxC=Math.max(data.maxC,6);
                const cell=(v,f='')=>({v,f,styleId:0,style:{font:{},border:{}},t:f?'n':(typeof v==='number'?'n':'s'),display:f?'='+f:String(v)});
                data.cells.set('A1',cell(10));data.cells.set('B1',cell(20));data.cells.set('C1',cell(30));
                data.cells.set('A2',cell('', 'SUM(A1:C1)'));
                data.cells.set('A3',cell('', 'B1'));
                data.cells.set('A4',cell('', 'IF(A1="B1",C1,0)'));
                data.cells.set('A5',cell('', 'sum(a1:c1)'));
                data.cells.set('A6',cell('', 'SUM(A1 : C1)'));
                data.cells.set('A7',cell('', 'Table1[B1]'));
                const summary=globalThis.LocalXLSX.createBlank().sheets[0];
                summary.name='Summary';summary.maxR=Math.max(summary.maxR,4);summary.maxC=Math.max(summary.maxC,2);
                summary.cells.set('A1',cell('', 'SUM(Data!A1:C1)'));
                summary.cells.set('B1',cell('', 'Data!B1'));
                summary.cells.set('C1',cell('', "SUM('Data'!$A$1:$C$1)"));
                book.sheets.push(summary);book.active=0;
                NS.FormulaEvaluator.recalculate(book);api.editor.render({rebuild:true});

                const formulas=()=>({
                    local:data.cells.get('A2')?.f,
                    single:data.cells.get('A3')?.f,
                    quotedLiteral:data.cells.get('A4')?.f,
                    lowercase:data.cells.get('A5')?.f,
                    spacedRange:data.cells.get('A6')?.f,
                    structured:data.cells.get('A7')?.f,
                    external:summary.cells.get('A1')?.f,
                    externalSingle:summary.cells.get('B1')?.f,
                    absolute:summary.cells.get('C1')?.f,
                });
                const selection=api.editor.selection, commands=api.editor.commands;
                selection.select(0,0,data,false);
                const inserted=commands.execute('structure.insertColumn');
                const afterInsert=formulas();
                commands.execute('edit.undo');
                const afterUndo=formulas();
                commands.execute('edit.redo');
                const afterRedo=formulas();

                selection.select(0,2,data,false);selection.select(0,3,data,true);
                const deleted=commands.execute('structure.deleteColumns');
                const afterDelete=formulas();
                commands.execute('edit.undo');
                const afterDeleteUndo=formulas();
                commands.execute('edit.redo');
                const afterDeleteRedo=formulas();

                commands.execute('edit.undo');
                const blob=await globalThis.LocalXLSX.saveCopy(book),bytes=await blob.arrayBuffer();
                const parsed=await globalThis.LocalXLSX.parseWorkbook(bytes,'xls-s1-columns.xlsx');
                const parsedData=parsed.sheets.find(s=>s.name==='Data'),parsedSummary=parsed.sheets.find(s=>s.name==='Summary');
                return {
                    inserted,deleted,afterInsert,afterUndo,afterRedo,afterDelete,afterDeleteUndo,afterDeleteRedo,
                    roundtrip:{
                        local:parsedData?.cells.get('A2')?.f||'',
                        single:parsedData?.cells.get('A3')?.f||'',
                        lowercase:parsedData?.cells.get('A5')?.f||'',
                        spacedRange:parsedData?.cells.get('A6')?.f||'',
                        structured:parsedData?.cells.get('A7')?.f||'',
                        summary:parsedSummary?.cells.get('A1')?.f||'',
                        externalSingle:parsedSummary?.cells.get('B1')?.f||'',
                        absolute:parsedSummary?.cells.get('C1')?.f||'',
                        blobSize:blob.size,
                    },
                    commandOwned:['structure.insertColumn','structure.deleteColumns','edit.undo','edit.redo'].every(id=>commands.has(id)),
                };
            }""")

            assert result["inserted"] is True, result
            assert result["deleted"] is True, result
            assert result["commandOwned"] is True, result
            assert result["afterInsert"] == {
                "local": "SUM(A1:D1)",
                "single": "C1",
                "quotedLiteral": 'IF(A1="B1",D1,0)',
                "lowercase": "sum(A1:D1)",
                "spacedRange": "SUM(A1:D1)",
                "structured": "Table1[B1]",
                "external": "SUM(Data!A1:D1)",
                "externalSingle": "Data!C1",
                "absolute": "SUM('Data'!$A$1:$D$1)",
            }, result
            assert result["afterUndo"] == {
                "local": "SUM(A1:C1)",
                "single": "B1",
                "quotedLiteral": 'IF(A1="B1",C1,0)',
                "lowercase": "sum(a1:c1)",
                "spacedRange": "SUM(A1 : C1)",
                "structured": "Table1[B1]",
                "external": "SUM(Data!A1:C1)",
                "externalSingle": "Data!B1",
                "absolute": "SUM('Data'!$A$1:$C$1)",
            }, result
            assert result["afterRedo"] == result["afterInsert"], result
            assert result["afterDelete"] == {
                "local": "SUM(A1:B1)",
                "single": "#REF!",
                "quotedLiteral": 'IF(A1="B1",#REF!,0)',
                "lowercase": "sum(A1:B1)",
                "spacedRange": "SUM(A1:B1)",
                "structured": "Table1[B1]",
                "external": "SUM(Data!A1:B1)",
                "externalSingle": "#REF!",
                "absolute": "SUM('Data'!$A$1:$B$1)",
            }, result
            assert result["afterDeleteUndo"] == result["afterInsert"], result
            assert result["afterDeleteRedo"] == result["afterDelete"], result
            assert result["roundtrip"]["local"] == "SUM(A1:D1)", result
            assert result["roundtrip"]["single"] == "C1", result
            assert result["roundtrip"]["lowercase"] == "sum(A1:D1)", result
            assert result["roundtrip"]["spacedRange"] == "SUM(A1:D1)", result
            assert result["roundtrip"]["structured"] == "Table1[B1]", result
            assert result["roundtrip"]["summary"] == "SUM(Data!A1:D1)", result
            assert result["roundtrip"]["externalSingle"] == "Data!C1", result
            assert result["roundtrip"]["absolute"] == "SUM('Data'!$A$1:$D$1)", result
            assert result["roundtrip"]["blobSize"] > 500, result
            assert not errors, errors
            browser.close()
        print(f"XLS-S1 structural columns ({browser_name}): OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
