#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ["pdf", "documents", "presentations", "txt", "epub", "spreadsheets"]
RUNTIME_ANCHOR = "9da9b798c624e3db6bcf933d85ed19892997bf5f"


def main() -> None:
    state = json.loads((ROOT / "STABILITY_STATE.json").read_text(encoding="utf-8"))
    assert state["program"] == "stability-functional-isolation", state
    assert state["currentWorkspace"] == "freeze", state
    assert state["completedWorkspaces"] == WORKSPACES, state
    candidate = state.get("freezeCandidate") or {}
    assert candidate.get("runtimeAnchor") == RUNTIME_ANCHOR, candidate
    assert candidate.get("status") in {"candidate", "frozen"}, candidate
    assert state["active"] in {True, False}

    baseline = (ROOT / "docs" / "STABILITY-FREEZE-2026-09-08.md").read_text(encoding="utf-8")
    assert RUNTIME_ANCHOR in baseline
    assert "A button is a command binding" in baseline or "a button is a command binding" in baseline
    for phase in ("PPT-P2", "XLS-S1", "XLS-S2"):
        assert phase in baseline, phase

    required = [
        "tests/test_pdf_stability_contract.py",
        "tests/test_documents_stability_contract.py",
        "tests/test_presentations_stability_contract.py",
        "tests/test_txt_stability_contract.py",
        "tests/test_epub_stability_contract.py",
        "tests/test_spreadsheets_stability_contract.py",
        "tests/test_cross_suite_stability_contract.py",
        "tests/test_pdf_stability_browser.py",
        "tests/test_documents_stability_browser.py",
        "tests/test_presentations_stability_browser.py",
        "tests/test_txt_stability_browser.py",
        "tests/test_epub_stability_browser.py",
        "tests/test_spreadsheets_stability_browser.py",
        "tests/test_cross_suite_stability_browser.py",
        "tests/test_security_pdfjs_config.py",
        "scripts/validate_suite_contracts.py",
        ".github/workflows/stability-freeze-regression.yml",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    assert not missing, "Missing freeze-gate artifacts:\n" + "\n".join(missing)

    print("Stability freeze contract: OK")


if __name__ == "__main__":
    main()
