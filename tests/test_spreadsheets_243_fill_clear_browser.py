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
            return {v:cell?.v??'',f:cell?.f??'',style:cell?.style||{}};
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


def main():
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

            # Backspace has the same clear semantics.
            select_range(page, 0, 0, 2, 0)
            page.locator("#contentViewport").focus()
            page.keyboard.press("Backspace")
            assert [x["v"] for x in cell_values(page, ["A1", "A2", "A3"])] == ["", "", ""]
            page.evaluate("()=>globalThis.__inkdosSpreadsheetsS1.editor.commands.execute('edit.undo')")

            # Single numeric seed copies its value down by default.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, e=api.editor.editor;
              e.commitValue('2',0,0); api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 0, 0, 0)
            drag_handle(page, "A4")
            assert [x["v"] for x in cell_values(page, ["A1", "A2", "A3", "A4"])] == [2, 2, 2, 2]

            # Two numeric seeds continue their arithmetic series.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, e=api.editor.editor;
              e.commitValue('1',0,0); e.commitValue('2',1,0); api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 0, 1, 0)
            drag_handle(page, "A5")
            assert [x["v"] for x in cell_values(page, ["A1", "A2", "A3", "A4", "A5"])] == [1, 2, 3, 4, 5]

            # Ctrl + one numeric seed explicitly requests a +1 series.
            page.evaluate("""()=>{
              const api=globalThis.__inkdosSpreadsheetsS1, e=api.editor.editor;
              e.commitValue('7',0,1); api.editor.render({rebuild:true});
            }""")
            select_range(page, 0, 1, 0, 1)
            drag_handle(page, "B4", ctrl=True)
            assert [x["v"] for x in cell_values(page, ["B1", "B2", "B3", "B4"])] == [7, 8, 9, 10]

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
