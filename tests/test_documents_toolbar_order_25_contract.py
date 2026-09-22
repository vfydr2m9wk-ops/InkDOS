#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"apps/documents/index.html").read_text(encoding="utf-8")
D1=(ROOT/"apps/documents/ui/d1-tools.js").read_text(encoding="utf-8")
def pos(token):
    i=HTML.find(token); assert i>=0, token; return i
def test_documents_final_toolbar_order():
    tokens=['id="undoBtn"','id="redoBtn"','id="printBtn"','id="formatPainterBtn"','id="zoomMenuBtn"','id="styleSelect"','id="fontSelect"','id="sizeSelect"','data-cmd="bold"','data-cmd="italic"','data-cmd="underline"','id="d1FormatBtn"','id="hyperlinkBtn"','id="commentBtn"','for="imageInput"','id="alignmentSelect"','id="lineSpacing"','id="checklistBtn"','data-cmd="insertUnorderedList"','data-cmd="insertOrderedList"','data-cmd="outdent"','data-cmd="indent"','id="clearFormattingBtn"']
    positions=[pos(t) for t in tokens]
    assert positions==sorted(positions)
def test_color_highlight_direct_contextual_surface():
    assert 'id="d1FormatBtn"' in HTML
    assert "formatBtn=$('d1FormatBtn')" in D1
    assert "d1FontColor" in D1 and "d1HighlightColor" in D1
    assert "applyCommand('foreColor'" in D1 and "applyHighlight" in D1
def test_image_is_direct_toolbar_action():
    assert 'for="imageInput"' in HTML and 'aria-label="Insert image"' in HTML
    assert pos('for="imageInput"') < pos('id="alignmentSelect"')
