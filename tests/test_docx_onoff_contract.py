from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_docx_onoff_properties_respect_explicit_false_values():
    parser = read("apps/documents/engine/docx-parser.js")
    assert "function onOff(" in parser
    assert "['0','false','off','no'].includes" in parser
    assert "if(onOff(first(pPr,'pageBreakBefore')))out.pageBreakBefore=true;" in parser
    assert "if(onOff(first(pPr,'keepNext')))out.keepNext=true;" in parser
