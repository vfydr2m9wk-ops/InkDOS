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


def write_state(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def main() -> None:
    original_base_state = scope.base_state
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STABILITY_STATE.json"
            frozen = state()
            write_state(path, frozen)

            # Before the frozen anchor reaches main, the promotion PR is allowed to
            # contain the six audited workspaces as one stability-freeze scope.
            scope.base_state = lambda _base: {}
            pending = scope.stability_scope(path, "origin/main")
            assert pending == ("stability:freeze", set(ORDER)), pending

            # Once the same frozen anchor is already in main, stability no longer
            # overrides the functional roadmap. Future work must return to the
            # normal one-workspace FUNCTIONAL_STATE scope.
            scope.base_state = lambda _base: frozen
            integrated = scope.stability_scope(path, "origin/main")
            assert integrated is None, integrated

            # An incomplete freeze must never receive the multi-workspace promotion
            # allowance, even when the anchor is not yet in main.
            scope.base_state = lambda _base: {}
            write_state(path, state(completed=ORDER[:-1]))
            try:
                scope.stability_scope(path, "origin/main")
            except SystemExit:
                pass
            else:
                raise AssertionError("Incomplete frozen stability state was accepted")

            write_state(path, state(status="candidate"))
            try:
                scope.stability_scope(path, "origin/main")
            except SystemExit:
                pass
            else:
                raise AssertionError("Non-frozen inactive stability state was accepted")
    finally:
        scope.base_state = original_base_state

    print("Phase-scope freeze lifecycle contract: OK")


if __name__ == "__main__":
    main()
