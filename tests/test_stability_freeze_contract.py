#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ["pdf", "documents", "presentations", "txt", "epub", "spreadsheets"]
LEGACY_RUNTIME_ANCHOR = "9da9b798c624e3db6bcf933d85ed19892997bf5f"
RUNTIME_ANCHOR = "44896f583d14dba6ba00b4ee1311f85ed513ad8a"
SUPERSEDED = "superseded-by-user-device-remediation"
REFREEZE_DOC = ROOT / "docs" / "STABILITY-FREEZE-2026-09-10.md"


def main() -> None:
    state = json.loads((ROOT / "STABILITY_STATE.json").read_text(encoding="utf-8"))
    assert state["program"] == "stability-functional-isolation", state
    assert state["active"] in {True, False}, state

    candidate = state.get("freezeCandidate") or {}
    remediation = state.get("remediation") or {}
    remediation_active = (
        state.get("active") is True
        and candidate.get("status") == SUPERSEDED
        and remediation.get("requiresCrossSuiteRevalidation") is True
    )

    if remediation_active:
        assert candidate.get("runtimeAnchor") == LEGACY_RUNTIME_ANCHOR, candidate
        completed = state.get("completedWorkspaces") or []
        assert completed == WORKSPACES[: len(completed)], state
        assert len(completed) <= len(WORKSPACES), state
        expected_current = WORKSPACES[len(completed)] if len(completed) < len(WORKSPACES) else "cross-suite"
        assert state.get("currentWorkspace") == expected_current, state
        assert remediation.get("startedAt"), remediation
        assert remediation.get("reason"), remediation
    else:
        assert state["currentWorkspace"] == "freeze", state
        assert state["completedWorkspaces"] == WORKSPACES, state
        assert candidate.get("status") in {"candidate", "frozen"}, candidate
        assert candidate.get("runtimeAnchor") == RUNTIME_ANCHOR, candidate
        assert candidate.get("crossSuiteRun") == 34457839525, candidate
        assert remediation.get("requiresCrossSuiteRevalidation") is False, remediation
        assert remediation.get("crossSuiteRevalidatedRun") == candidate.get("crossSuiteRun"), remediation
        assert remediation.get("completedAt"), remediation
        if candidate.get("status") == "frozen":
            assert state["active"] is False, state
            assert candidate.get("freezeGateCommit"), candidate
            assert candidate.get("freezeGateRun"), candidate

    baseline_path = REFREEZE_DOC if REFREEZE_DOC.is_file() else ROOT / "docs" / "STABILITY-FREEZE-2026-09-08.md"
    baseline = baseline_path.read_text(encoding="utf-8")
    expected_anchor = RUNTIME_ANCHOR if REFREEZE_DOC.is_file() else LEGACY_RUNTIME_ANCHOR
    assert expected_anchor in baseline
    assert "A button is a command binding" in baseline or "a button is a command binding" in baseline
    for phase in ("PPT-P2", "XLS-S1", "XLS-S2"):
        assert phase in baseline, phase

    sw = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert "inkdos-v2.0.12-stability-" in sw, "Frozen baseline must retain a stability cache namespace"
    validator = (ROOT / "scripts" / "validate_repository.py").read_text(encoding="utf-8")
    assert "def frozen_stability():" in validator
    assert "if stability or frozen:" in validator
    assert "candidate.get('status')=='frozen'" in validator
    assert "state.get('completedWorkspaces')==FROZEN_WORKSPACES" in validator

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

    print("Stability freeze/remediation lifecycle contract: OK")


if __name__ == "__main__":
    main()
