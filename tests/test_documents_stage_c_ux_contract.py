from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D2 = (ROOT / "apps/documents/ui/d2-tools.js").read_text(encoding="utf-8")
RULER = (ROOT / "apps/documents/ui/ruler-controller.js").read_text(encoding="utf-8")
INDEX = (ROOT / "apps/documents/index.html").read_text(encoding="utf-8")


def test_document_tools_uses_semantic_control_not_phase_jargon():
    assert "button.textContent='P1'" not in D2
    assert "<strong>Document P1</strong>" not in D2
    assert "Document tools" in D2
    assert "aria-label','Document tools'" in D2 or 'aria-label="Document tools"' in D2
    assert "<svg" in D2


def test_ruler_exposes_scaled_numeric_labels():
    # Labels must be generated from the current page/content geometry rather than
    # hard-coded visual ticks, so they remain meaningful as the ruler scales.
    assert "ruler-label" in RULER
    assert "contentWidthPx" in RULER
    assert "getBoundingClientRect" in RULER
    assert "replaceChildren" in RULER or "textContent" in RULER
    assert 'aria-label="Paragraph ruler"' in INDEX


if __name__ == "__main__":
    test_document_tools_uses_semantic_control_not_phase_jargon()
    test_ruler_exposes_scaled_numeric_labels()
    print("documents Stage-C UX contract: PASS")
