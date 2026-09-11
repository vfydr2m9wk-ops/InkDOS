from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXT = ROOT / "apps" / "txt"
STYLES = (TXT / "styles.css").read_text(encoding="utf-8")
CONTROLS = (TXT / "ui" / "txt-controls.js").read_text(encoding="utf-8")


def test_wrap_pressed_state_is_semantic_but_not_global_accent_active_state():
    # Wrap is a persistent view preference, not a selected command. Keep the
    # semantic aria-pressed state, but give it a TXT-local neutral pressed
    # treatment instead of the generic accent-heavy .tool-btn.active skin.
    assert "setAttribute('aria-pressed',String(!!detail.wrap))" in CONTROLS
    assert "classList.toggle('active',!!detail.wrap)" in CONTROLS
    assert "#wrapBtn.active" in STYLES
    assert "background:var(--txt-surface-soft)" in STYLES
    assert "border-color:var(--txt-line-strong)" in STYLES
    assert "color:var(--txt-text)" in STYLES


if __name__ == "__main__":
    test_wrap_pressed_state_is_semantic_but_not_global_accent_active_state()
    print("TXT Stage-C visual contract: PASS")
