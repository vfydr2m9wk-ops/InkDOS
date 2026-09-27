#!/usr/bin/env python3
"""The faster XLSX XML lookup helpers (localOne/localAll/childText) return exactly what the
previous array-based implementations returned: same elements, same document order, any
namespace or prefix, descendants only."""
from __future__ import annotations
import os, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "apps/spreadsheets/io/xlsx-engine.js").read_text(encoding="utf-8")
CURRENT = "\n".join(re.search(rf"function {name}\(.*", SRC).group(0) for name in ("childText", "localOne", "localAll"))
LEGACY = r"""
function legacyChildText(node,name){if(!node)return'';const n=[...node.children].find(x=>x.localName===name);return n?n.textContent:''}
function legacyLocalOne(node,name){return node?[...node.querySelectorAll('*')].find(n=>n.localName===name):null}
function legacyLocalAll(node,name){return node?[...node.querySelectorAll('*')].filter(n=>n.localName===name):[]}
"""
XML = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:x14="http://schemas.microsoft.com/office/spreadsheetml/2009/9/main" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">
<dimension ref="A1:B3"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1"/></sheetView></sheetViews>
<cols><col min="1" max="1" width="12"/><col min="2" max="2" width="9"/></cols>
<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><f>SUM(B2:B3)</f><v>3</v></c></row>
<row r="2"><c r="A2" t="inlineStr"><is><t>two</t></is></c><c r="B2"><v>1</v></c></row><row r="3"><c r="B3"><v>2</v></c></row></sheetData>
<mergeCells count="1"><mergeCell ref="A1:A2"/></mergeCells><hyperlinks><hyperlink ref="A3" r:id="rId1"/></hyperlinks>
<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/><drawing r:id="rId2"/>
<extLst><ext uri="{x}"><x14:conditionalFormattings><x14:conditionalFormatting><x14:cfRule type="dataBar"/></x14:conditionalFormatting></x14:conditionalFormattings></ext></extLst>
</worksheet>"""
NAMES = ["worksheet", "dimension", "pane", "col", "sheetData", "row", "c", "v", "f", "t", "is", "mergeCells", "mergeCell",
         "hyperlink", "pageMargins", "drawing", "extLst", "cfRule", "conditionalFormatting", "missing"]

def main():
    browser_name = os.environ.get("BROWSER", "chromium")
    with sync_playwright() as pw:
        browser = getattr(pw, browser_name).launch(headless=True)
        page = browser.new_page()
        page.set_content("<!doctype html><title>x</title>")
        result = page.evaluate(
            """([code, legacy, xml, names]) => {
              const api = new Function(code + legacy + '; return {childText, localOne, localAll, legacyChildText, legacyLocalOne, legacyLocalAll};')();
              const doc = new DOMParser().parseFromString(xml, 'application/xml');
              const all = [...doc.querySelectorAll('*')];
              const id = n => n ? all.indexOf(n) : -1;
              const roots = [doc, doc.documentElement, ...all];
              const mismatches = [];
              for (const root of roots) for (const name of names) {
                const one = api.localOne(root, name), legacyOne = api.legacyLocalOne(root, name);
                const a = one === undefined ? 'undefined' : id(one), b = legacyOne === undefined ? 'undefined' : id(legacyOne);
                const c = api.localAll(root, name).map(id).join(), d = api.legacyLocalAll(root, name).map(id).join();
                if (a !== b || c !== d) mismatches.push([id(root), name, a, b, c, d]);
                if (root !== doc && api.childText(root, name) !== api.legacyChildText(root, name)) mismatches.push([id(root), name, 'childText']);
              }
              for (const fn of ['localOne', 'localAll', 'childText']) {
                if (JSON.stringify(api[fn](null, 'row')) !== JSON.stringify(api['legacy' + fn[0].toUpperCase() + fn.slice(1)](null, 'row'))) mismatches.push(['null', fn]);
              }
              return {checked: roots.length * names.length, mismatches: mismatches.slice(0, 10)};
            }""",
            [CURRENT, LEGACY, XML, NAMES],
        )
        browser.close()
    assert result["checked"] > 400 and result["mismatches"] == [], result
    print(f"Spreadsheets XML lookup equivalence ({browser_name}): OK {result['checked']} lookups")

if __name__ == "__main__":
    main()
