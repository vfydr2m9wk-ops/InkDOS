#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"apps"/"documents"
def r(p): return p.read_text(encoding="utf-8")
def test_print_toolbar_contract():
    html=r(DOC/"index.html"); app=r(DOC/"app.js"); controller=r(DOC/"ui"/"command-controller.js"); d1=r(DOC/"ui"/"d1-tools.js")
    assert 'id="printBtn"' in html and 'aria-label="Print"' in html
    assert html.index('id="redoBtn"') < html.index('id="printBtn"') < html.index('id="formatPainterBtn"')
    assert "commandRegistry.register('file.print',()=>d1.print())" in app
    assert "bindClick('printBtn','file.print')" in controller
    assert "function exportPdf()" in d1 and "setTimeout(()=>global.print(),20)" in d1
    assert "print:exportPdf" in d1
if __name__=='__main__': test_print_toolbar_contract(); print('Documents 2.5 direct Print toolbar contract passed.')
