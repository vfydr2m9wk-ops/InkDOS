#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/"apps"/"pdf"

def read(path): return path.read_text(encoding="utf-8")

def main():
    html=read(PDF/"index.html")
    reader=read(PDF/"ui"/"reader-tools.js")
    pages=read(PDF/"ui"/"page-tools.js")
    modes=read(PDF/"ui"/"mode-bindings.js")
    css=read(PDF/"ui"/"pdf-toolbar.css")

    # The toolbar follows one stable visual hierarchy. Contextual annotation controls
    # come first; reading/navigation follows; global document actions remain last.
    ordered=[
        'id="pdfHistoryGroup"',
        'id="pdfAnnotationTools"',
        'id="pdfTextProperties"',
        'id="pdfPenProperties"',
        'id="pdfNavigationGroup"',
        'id="pdfViewGroup"',
        'id="pdfUtilityGroup"',
    ]
    positions=[html.index(x) for x in ordered]
    assert positions==sorted(positions), positions

    # High-frequency reader/document controls are projected into explicit hosts,
    # rather than relying on whichever generic tool-group happens to contain zoom.
    assert "$('pdfViewGroup')" in reader
    assert "$('pdfUtilityGroup')" in reader
    assert "view.appendChild(rotateBtn)" in reader
    assert "utility.insertBefore(searchBtn" in reader
    assert "utility.insertBefore(printBtn" in reader

    # Page structure remains adjacent to navigation and compact in the rail.
    assert "button.className='tool-btn icon-only'" in pages
    assert "button.title='Organize pages'" in pages
    assert "nav.insertAdjacentElement('afterend',button)" in pages

    # Annotation order is explicit: highlight before underline, note/delete after it.
    assert "oldHighlight?.insertAdjacentElement('afterend',highlightBtn)" in modes
    assert "(underline||highlightBtn).insertAdjacentElement('afterend',noteBtn)" in modes
    assert "noteBtn.insertAdjacentElement('afterend',deleteBtn)" in modes

    # Annotation tools use compact icon geometry while keeping accessible labels/tooltips.
    assert ".pdf-annotation-tools .tool-label{display:none}" in css
    assert 'title="Add text annotation"' in html
    assert 'title="Underline PDF text"' in html
    assert 'title="Save PDF copy"' in html

    print("PDF 2.5 toolbar organization contract passed.")

if __name__=="__main__": main()
