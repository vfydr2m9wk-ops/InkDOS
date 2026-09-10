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
PORT = 8796
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local Spreadsheet XLS-S2 test server did not start")


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
                const book=api.session.book, sheet=book.sheets[0], editor=api.editor, commands=editor.commands;
                sheet.maxR=Math.max(sheet.maxR,6);sheet.maxC=Math.max(sheet.maxC,6);
                const cell=(v,f='',style={})=>({v,f,styleId:0,style:{font:{},border:{},...style},t:f?'n':(typeof v==='number'?'n':'s'),display:f?'='+f:String(v)});
                sheet.cells.set('A1',cell(10));
                sheet.cells.set('B1',cell('', 'A1+$C$3+D$4+$E5',{font:{bold:true},border:{}}));
                sheet.cells.set('A2',cell('label'));
                NS.FormulaEvaluator.recalculate(book);editor.render({rebuild:true});

                editor.selection.select(0,0,sheet,false);editor.selection.select(1,1,sheet,true);
                const payload=commands.execute('edit.copyPayload');
                editor.selection.select(2,2,sheet,false);
                const pasted=commands.execute('edit.pastePayload',payload);
                const afterPaste={
                    c3:sheet.cells.get('C3')?.v,
                    d3f:sheet.cells.get('D3')?.f,
                    c4:sheet.cells.get('C4')?.v,
                    d3Bold:!!sheet.cells.get('D3')?.style?.font?.bold,
                };
                commands.execute('edit.undo');
                const afterUndo={c3:sheet.cells.has('C3'),d3:sheet.cells.has('D3'),c4:sheet.cells.has('C4')};
                commands.execute('edit.redo');
                const afterRedo={c3:sheet.cells.get('C3')?.v,d3f:sheet.cells.get('D3')?.f,c4:sheet.cells.get('C4')?.v};
                const blob=await globalThis.LocalXLSX.saveCopy(book),bytes=await blob.arrayBuffer();
                const parsed=await globalThis.LocalXLSX.parseWorkbook(bytes,'xls-s2-clipboard.xlsx');
                const parsedSheet=parsed.sheets[0];
                return {payload,pasted,afterPaste,afterUndo,afterRedo,roundtrip:{d3f:parsedSheet.cells.get('D3')?.f||'',c3:parsedSheet.cells.get('C3')?.v,c4:parsedSheet.cells.get('C4')?.v,blobSize:blob.size},commands:commands.list()};
            }""")

            assert result["pasted"] is True, result
            assert result["payload"]["kind"] == "inkdos-spreadsheet-cells", result
            assert result["afterPaste"] == {"c3": 10, "d3f": "C3+$C$3+F$4+$E7", "c4": "label", "d3Bold": True}, result
            assert result["afterUndo"] == {"c3": False, "d3": False, "c4": False}, result
            assert result["afterRedo"] == {"c3": 10, "d3f": "C3+$C$3+F$4+$E7", "c4": "label"}, result
            assert result["roundtrip"]["d3f"] == "C3+$C$3+F$4+$E7", result
            assert result["roundtrip"]["c3"] == 10, result
            assert result["roundtrip"]["c4"] == "label", result
            assert result["roundtrip"]["blobSize"] > 500, result
            assert "edit.copyPayload" in result["commands"] and "edit.pastePayload" in result["commands"], result
            assert not errors, errors
            browser.close()
        print(f"XLS-S2 semantic clipboard ({browser_name}): OK")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
