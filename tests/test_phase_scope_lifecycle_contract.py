#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_phase_scope.py"

spec = importlib.util.spec_from_file_location("validate_phase_scope", SCRIPT)
assert spec and spec.loader
scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)

ORDER = ["pdf", "documents", "presentations", "txt", "epub", "spreadsheets"]
ANCHOR = "test-runtime-anchor"
ROADMAP = scope.FUNCTIONAL_ROADMAP


def state(*, completed=None, status="frozen") -> dict:
    return {
        "schemaVersion": 1,
        "program": "stability-functional-isolation",
        "active": False,
        "auditOrder": ORDER + ["cross-suite", "freeze"],
        "completedWorkspaces": ORDER if completed is None else completed,
        "currentWorkspace": "freeze",
        "freezeCandidate": {"status": status, "runtimeAnchor": ANCHOR},
    }


def functional_state(phase: str) -> dict:
    index = next(i for i, item in enumerate(ROADMAP) if item[0] == phase)
    current_phase, workspace = ROADMAP[index]
    value = {
        "schemaVersion": 1,
        "roadmap": "home-functional",
        "architectureContract": "physical-workspace-isolation",
        "transitionGateRequired": True,
        "completedPhases": [item[0] for item in ROADMAP[:index]],
        "currentPhase": {"id": current_phase, "workspace": workspace, "status": "active"},
    }
    if index + 1 < len(ROADMAP):
        next_phase, next_workspace = ROADMAP[index + 1]
        value["nextPhase"] = {"id": next_phase, "workspace": next_workspace}
    return value


def write_state(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def expect_rejected(callback, message: str) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise AssertionError(message)


def main() -> None:
    original_base_state = scope.base_state
    original_base_json_state = scope.base_json_state
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STABILITY_STATE.json"
            frozen = state()
            write_state(path, frozen)

            scope.base_state = lambda _base: {}
            pending = scope.stability_scope(path, "origin/main")
            assert pending == ("stability:freeze", set(ORDER)), pending

            scope.base_state = lambda _base: frozen
            integrated = scope.stability_scope(path, "origin/main")
            assert integrated is None, integrated

            scope.base_state = lambda _base: {}
            write_state(path, state(completed=ORDER[:-1]))
            expect_rejected(
                lambda: scope.stability_scope(path, "origin/main"),
                "Incomplete frozen stability state was accepted",
            )

            write_state(path, state(status="candidate"))
            expect_rejected(
                lambda: scope.stability_scope(path, "origin/main"),
                "Non-frozen inactive stability state was accepted",
            )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "FUNCTIONAL_STATE.json"
            xls_s1 = functional_state("XLS-S1")
            xls_s2 = functional_state("XLS-S2")
            audit = functional_state("Audit")

            write_state(path, audit)
            scope.base_json_state = lambda _base, filename: xls_s2 if filename == "FUNCTIONAL_STATE.json" else {}
            transition = scope.functional_scope(path, "origin/main")
            assert transition == ("XLS-S2", {"spreadsheets"}), transition

            # Main can legitimately lag one state-only transition while both
            # completed functional slices belong to the same physical workspace.
            scope.base_json_state = lambda _base, filename: xls_s1 if filename == "FUNCTIONAL_STATE.json" else {}
            multi = scope.functional_scope(path, "origin/main")
            assert multi == ("XLS-S1→XLS-S2", {"spreadsheets"}), multi

            scope.base_json_state = lambda _base, filename: audit if filename == "FUNCTIONAL_STATE.json" else {}
            integrated_audit = scope.functional_scope(path, "origin/main")
            assert integrated_audit == ("Audit", set()), integrated_audit

            # A multi-step promotion may never silently span different app roots.
            ppt_p2 = functional_state("PPT-P2")
            scope.base_json_state = lambda _base, filename: ppt_p2 if filename == "FUNCTIONAL_STATE.json" else {}
            expect_rejected(
                lambda: scope.functional_scope(path, "origin/main"),
                "Cross-workspace multi-phase promotion was accepted",
            )

            # Sequential state remains canonical: missing a completed phase is invalid.
            broken = functional_state("Audit")
            broken["completedPhases"] = broken["completedPhases"][:-1]
            write_state(path, broken)
            scope.base_json_state = lambda _base, filename: xls_s1 if filename == "FUNCTIONAL_STATE.json" else {}
            expect_rejected(
                lambda: scope.functional_scope(path, "origin/main"),
                "Functional state with a skipped completion was accepted",
            )
    finally:
        scope.base_state = original_base_state
        scope.base_json_state = original_base_json_state

    print("Phase-scope freeze and canonical functional transition lifecycle contract: OK")


if __name__ == "__main__":
    main()
