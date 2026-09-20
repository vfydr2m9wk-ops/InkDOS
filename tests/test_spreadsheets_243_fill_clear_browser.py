#!/usr/bin/env python3
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8785
BASE = f"http://127.0.0.1:{PORT}"


def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Spreadsheet test server did not start")


def cell_values(page, refs):
    return page.evaluate(
        """refs=>{
          const api=globalThis.__inkdosSpreadsheetsS1;
          const sheet=api.session.activeSheet();
          return refs.map(ref=>{
            const cell=sheet.cells.get(ref);
            return {v:cell?.v??'',f:cell?.f??'',t:cell?.t??'',display:cell?.display??'',style:cell?.style||{}};
          });
        }""",
        refs,
    )


def select_range(page, r1, c1, r2, c2):
    page.evaluate(
        """p=>{
          const api=globalThis.__inkdosSpreadsheetsS1, sheet=api.session.activeSheet();
          api.editor.selection.select(p.r1,p.c1,sheet,false);
          api.editor.selection.select(p.r2,p.c2,sheet,true);
          api.editor.selectionChanged();
        }""",
        {"r1": r1, "c1": c1, "r2": r2, "c2": c2},
    )


def drag_handle(page, target_ref, ctrl=False):
    handle = page.locator(".fill-handle")
    assert handle.count() == 1, "selected range must expose one fill handle"
    box = handle.bounding_box()
    target = page.locator(f'.cell[data-ref="{target_ref}"]')
    target_box = target.bounding_box()
    assert box and target_box
    if ctrl:
        page.keyboard.down("Control")
    try:
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.down()
        page.mouse.move(target_box["x"] + target_box["width"] / 2, target_box["y"] + target_box["height"] / 2, steps=5)
        page.mouse.up()
    finally:
        if ctrl:
            page.keyboard.up("Control")


def assert_fill_pointer_preview_contracts():
    source = (ROOT / "apps/spreadsheets/view/grid-surface.js").read_text(encoding="utf-8")
    assert "window.addEventListener('pointermove',e=>this.trackFillPointer(e))" in source, "fill drag must track pointermove under pointer capture"
    assert "document.elementFromPoint(e.clientX,e.clientY)" in source, "fill pointermove must hit-test coordinates"
    assert "plan=fillPreviewPlan(q,state.target)" in source, "fill preview must use the same dominant-axis plan as committed fill"
    assert "vertical>=horizontal" in source, "fill preview dominant-axis tie-break must match fillPlan"


def assert_date_system_contracts():
    xlsx = (ROOT / "apps/spreadsheets/io/xlsx-engine.js").read_text(encoding="utf-8")
    xls = (ROOT / "apps/spreadsheets/io/xls-biff8-engine.js").read_text(encoding="utf-8")
    controller = (ROOT / "apps/spreadsheets/ui/editor-controller.js").read_text(encoding="utf-8")
    assert "getAttribute('date1904')==='1'" in xlsx, "XLSX parser must retain workbook 1904 date-system metadata"
    assert "legacy:true,date1904" in xls, "BIFF8 parser must expose its decoded 1904 date-system metadata"
    assert "session.book?.date1904?Date.UTC(1904,0,1):Date.UTC(1899,11,30)" in controller, "fill display formatting must honor workbook date system"


def main():
    assert_fill_pointer_preview_contracts()
    assert_date_system_contracts()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + "/apps/spreadsheets/?suite=1", wait_until="load")
            page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1")
            page.click("#startNew")
            page.wait_for_function("() => !!globalThis.__inkdosSpreadsheetsS1.session.book?.loaded")
            page.wait_for_selector('.cell[data-ref="A1"]')

            # Delete clears the full selected range in one undo action and preserves formatting.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, e=api.editor.editor;
              e.commitValue('11',0,0); e.commitValue('22',1,0); e.commitValue('33',2,0);
              const c=api.session.activeSheet().cells.get('A2');
              c.style={...(c.style||{}),font:{...((c.style||{}).font||{}),bold:true}};
              api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 0, 2, 0)
            page.locator("#contentViewport").focus()
            page.keyboard.press("Delete")
            cleared = cell_values(page, ["A1", "A2", "A3"])
            assert [x["v"] for x in cleared] == ["", "", ""], cleared
            assert cleared[1]["style"].get("font", {}).get("bold") is True, cleared
            page.evaluate("()=>globalThis.__inkdosSpreadsheetsS1.editor.commands.execute('edit.undo')")
            restored = cell_values(page, ["A1", "A2", "A3"])
            assert [x["v"] for x in restored] == [11, 22, 33], restored

            select_range(page, 0, 0, 2, 0)
            page.locator("#contentViewport").focus()
            page.keyboard.press("Backspace")
            assert [x["v"] for x in cell_values(page, ["A1", "A2", "A3"])] == ["", "", ""]
            page.evaluate("()=>globalThis.__inkdosSpreadsheetsS1.editor.commands.execute('edit.undo')")

            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, e=api.editor.editor;
              e.commitValue('2',0,0); api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 0, 0, 0)
            drag_handle(page, "A4")
            assert [x["v"] for x in cell_values(page, ["A1", "A2", "A3", "A4"])] == [2, 2, 2, 2]

            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, e=api.editor.editor;
              e.commitValue('1',0,0); e.commitValue('2',1,0); api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 0, 1, 0)
            drag_handle(page, "A5")
            assert [x["v"] for x in cell_values(page, ["A1", "A2", "A3", "A4", "A5"])] == [1, 2, 3, 4, 5]

            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, e=api.editor.editor;
              e.commitValue('7',0,1); api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 1, 0, 1)
            drag_handle(page, "B4", ctrl=True)
            assert [x["v"] for x in cell_values(page, ["B1", "B2", "B3", "B4"])] == [7, 8, 9, 10]

            # Imported boolean seeds must copy/cycle, never coerce TRUE/FALSE into a numeric series.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, s=api.session.activeSheet();
              s.cells.set('C1',{v:true,f:'',t:'b',styleId:0,style:{},display:'TRUE'});
              s.cells.set('C2',{v:false,f:'',t:'b',styleId:0,style:{},display:'FALSE'});
              api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 2, 1, 2)
            drag_handle(page, "C4")
            logical = cell_values(page, ["C1", "C2", "C3", "C4"])
            assert [x["v"] for x in logical] == [True, False, True, False], logical
            assert [x["t"] for x in logical] == ["b", "b", "b", "b"], logical

            # Imported numeric text must remain text and cycle rather than becoming numeric series cells.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, s=api.session.activeSheet();
              s.cells.set('D1',{v:'1',f:'',t:'s',styleId:0,style:{},display:'1'});
              s.cells.set('D2',{v:'2',f:'',t:'s',styleId:0,style:{},display:'2'});
              api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 3, 1, 3)
            drag_handle(page, "D4")
            text = cell_values(page, ["D1", "D2", "D3", "D4"])
            assert [x["v"] for x in text] == ["1", "2", "1", "2"], text
            assert [x["t"] for x in text] == ["s", "s", "s", "s"], text

            # Numeric-series generation cycles source formatting instead of collapsing to an endpoint style.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, s=api.session.activeSheet();
              s.cells.set('E1',{v:10,f:'',t:'n',styleId:1,style:{font:{bold:true}},display:'10'});
              s.cells.set('E2',{v:20,f:'',t:'n',styleId:2,style:{font:{italic:true}},display:'20'});
              api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 4, 1, 4)
            drag_handle(page, "E6")
            styled = cell_values(page, ["E1", "E2", "E3", "E4", "E5", "E6"])
            assert [x["v"] for x in styled] == [10, 20, 30, 40, 50, 60], styled
            assert [x["style"].get("font", {}).get("bold", False) for x in styled] == [True, False, True, False, True, False], styled
            assert [x["style"].get("font", {}).get("italic", False) for x in styled] == [False, True, False, True, False, True], styled

            # Generated numeric-series cells must refresh display using the cycled number format.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, s=api.session.activeSheet();
              s.cells.set('F1',{v:.1,f:'',t:'n',styleId:10,style:{numFmtId:10},display:'10.00%'});
              s.cells.set('F2',{v:.2,f:'',t:'n',styleId:10,style:{numFmtId:10},display:'20.00%'});
              api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 5, 1, 5)
            drag_handle(page, "F4")
            percent = cell_values(page, ["F1", "F2", "F3", "F4"])
            assert [round(x["v"], 8) for x in percent] == [.1, .2, .3, .4], percent
            assert [x["display"] for x in percent] == ["10.00%", "20.00%", "30.00%", "40.00%"], percent

            # 1904-system workbooks must format generated date-series values against the 1904 epoch.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, s=api.session.activeSheet();
              api.session.book.date1904=true;
              s.cells.set('G1',{v:0,f:'',t:'n',styleId:14,style:{numFmtId:14},display:'01/01/1904'});
              s.cells.set('G2',{v:1,f:'',t:'n',styleId:14,style:{numFmtId:14},display:'02/01/1904'});
              api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 6, 1, 6)
            drag_handle(page, "G4")
            dates1904 = cell_values(page, ["G1", "G2", "G3", "G4"])
            assert [x["v"] for x in dates1904] == [0, 1, 2, 3], dates1904
            assert [x["display"] for x in dates1904] == ["01/01/1904", "02/01/1904", "03/01/1904", "04/01/1904"], dates1904
            api_date_system = page.evaluate("()=>globalThis.__inkdosSpreadsheetsS1.session.book.date1904")
            assert api_date_system is True

            browser.close()
        print("Spreadsheets 2.4.3 fill/clear browser regression passed.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
