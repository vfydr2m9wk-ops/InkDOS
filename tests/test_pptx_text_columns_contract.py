from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pptx_multicolumn_text_is_preserved_and_rendered_across_views():
    parser = read("apps/presentations/io/pptx-open-controller.js")
    model = read("apps/presentations/engine/presentation-session.js")
    surface = read("apps/presentations/view/slide-surface.js")
    thumbs = read("apps/presentations/ui/slide-panel-controller.js")
    slideshow = read("apps/presentations/presentation/slideshow-controller.js")

    # DrawingML a:bodyPr may define numCol/spcCol. Import must retain that
    # geometry instead of flattening a multi-column text frame into one column.
    assert "numCol" in parser
    assert "columnCount" in parser
    assert "spcCol" in parser
    assert "columnSpacingEmu" in parser

    # The normalized text object and its preservation signature must keep the
    # imported column geometry stable through session snapshots/edits/saves.
    assert "columnCount" in model
    assert "columnSpacingEmu" in model
    assert "columnCount:sane(o.columnCount,1)" in model

    # Editor, thumbnail strip, and slideshow must all project the same column
    # count. The editor/slideshow additionally constrain height so CSS columns
    # flow vertically before advancing to the next column.
    assert "style.columnCount" in surface
    assert "style.columnGap" in surface
    assert "style.columnFill='auto'" in surface
    assert "style.height='100%'" in surface
    assert "style.columnCount" in thumbs
    assert "style.columnCount" in slideshow
    assert "style.columnFill='auto'" in slideshow
