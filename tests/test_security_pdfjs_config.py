from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pdfjs_eval_and_scripting_are_explicitly_disabled():
    source = (ROOT / "apps/pdf/io/file-open-controller.js").read_text(encoding="utf-8")
    assert "isEvalSupported:false" in source or "isEvalSupported: false" in source
    assert "isEvalSupported:true" not in source
    assert "isEvalSupported: true" not in source
    assert "enableScripting:false" in source or "enableScripting: false" in source
    assert "enableScripting:true" not in source
    assert "enableScripting: true" not in source


def test_pdfjs_vendor_provenance_is_declared():
    provenance = (ROOT / "apps/pdf/vendor/pdfjs/VENDOR-PROVENANCE.txt").read_text(encoding="utf-8")
    assert "Upstream project: Mozilla PDF.js" in provenance
    assert "Vendored display/runtime version:" in provenance
