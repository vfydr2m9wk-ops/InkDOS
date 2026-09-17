from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MODULE = "apps/presentations/io/pptx-text-columns.js"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pptx_multicolumn_text_is_preserved_and_rendered_across_views():
    app = read("apps/presentations/app.js")
    columns = read(MODULE)

    # The runtime must load the local-only fidelity module; no network or
    # backend conversion is allowed.
    assert "io/pptx-text-columns.js" in app
    assert "PptxTextColumns" in app

    # DrawingML a:bodyPr numCol/spcCol are read directly from the opened PPTX.
    assert "numCol" in columns
    assert "spcCol" in columns
    assert "columnCount" in columns
    assert "columnSpacingEmu" in columns

    # The same imported geometry is projected to editor, thumbnails, and
    # slideshow so a multi-column frame is not flattened into one column.
    assert "editorColumns" in columns
    assert "thumbnailColumns" in columns
    assert "slideshowColumns" in columns
    assert "style.columnCount" in columns
    assert "style.columnGap" in columns
    assert "style.columnFill='auto'" in columns
    assert "style.height='100%'" in columns

    subprocess.run(["node", "--check", str(ROOT / MODULE)], check=True)


if __name__ == "__main__":
    test_pptx_multicolumn_text_is_preserved_and_rendered_across_views()
