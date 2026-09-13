#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

EXPECTED = {
    "apply-inkdos-update.yml",
    "desktop-tauri.yml",
    "refresh-integrity-metadata.yml",
    "release.yml",
    "stability-freeze-regression.yml",
}

REQUIRED_VALIDATOR_FRAGMENTS = (
    "name: InkDOS validation",
    "python scripts/run_release_validation.py",
    "python tests/test_update_trust_boundary.py",
    "tests/test_*_contract.py",
    "tests/test_*_stability_browser.py",
    "tests/test_pdf_stability_frame.py",
    "tests/test_pdf_stability_comments.py",
    "tests/test_pdf_stability_offline.py",
    "tests/test_pptx_security_browser.py",
    "tests/test_ppt_p2_transitions_browser.py",
    "tests/test_ppt_p2_notes_browser.py",
    "tests/test_ppt_p2_theme_browser.py",
    "tests/test_ppt_p2_tables_browser.py",
    "tests/test_ppt_p2_table_structure_browser.py",
    "tests/test_ppt_p2_table_merge_browser.py",
    "tests/test_ppt_p2_table_format_browser.py",
    "tests/test_ppt_p2_table_style_browser.py",
    "tests/test_ppt_p2_table_tools_ui_browser.py",
    "tests/test_xls_s1_structural_formulas_browser.py",
    "tests/test_xls_s1_structural_columns_browser.py",
    "tests/test_xls_s2_clipboard_browser.py",
    "tests/test_*roundtrip.py",
)


def main() -> None:
    actual = {path.name for path in WORKFLOWS.glob("*.yml")}
    assert actual == EXPECTED, (
        "GitHub Actions surface drifted. "
        f"expected={sorted(EXPECTED)} actual={sorted(actual)}"
    )

    validator = (WORKFLOWS / "stability-freeze-regression.yml").read_text(encoding="utf-8")
    missing = [item for item in REQUIRED_VALIDATOR_FRAGMENTS if item not in validator]
    assert not missing, f"Permanent validator is missing required coverage markers: {missing}"

    update = (WORKFLOWS / "apply-inkdos-update.yml").read_text(encoding="utf-8")
    integrity = (WORKFLOWS / "refresh-integrity-metadata.yml").read_text(encoding="utf-8")
    desktop = (WORKFLOWS / "desktop-tauri.yml").read_text(encoding="utf-8")
    release = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")

    assert "contents: write" in update, "Transactional update workflow lost its write boundary."
    assert "contents: write" in integrity, "Integrity metadata workflow lost its write boundary."
    assert "permissions:\n  contents: read" in validator, "Permanent validator must remain read-only."
    assert "permissions:\n  contents: read" in desktop, "Desktop validation/build workflow must remain read-only."
    assert "permissions:\n  contents: read" in release, "Unified release workflow must default to read-only."
    assert "publish:" in release and "contents: write" in release, (
        "Unified release workflow must confine write access to its publication job."
    )

    print("Minimal GitHub Actions workflow contract passed.")


if __name__ == "__main__":
    main()
