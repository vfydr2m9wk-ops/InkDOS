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


def write_state(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def state(paths: list[str], *, active: bool = True, gate: str = "blocked") -> dict:
    return {
        "schemaVersion": 1,
        "program": "security-remediation",
        "active": active,
        "securityGate": gate,
        "baseBranch": "main",
        "scopePolicy": "functional-plus-explicit-security-exceptions",
        "allowedExactPaths": paths,
        "rationale": {item: f"Security remediation for {item}" for item in paths},
    }


def rejected(path: Path, value: dict) -> bool:
    write_state(path, value)
    try:
        scope.security_exact_exceptions(path)
    except SystemExit:
        return True
    return False


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SECURITY_REMEDIATION_STATE.json"

        exact = ["apps/pdf/io/file-open-controller.js", "index.html"]
        write_state(path, state(exact))
        assert scope.security_exact_exceptions(path) == set(exact)

        write_state(path, state([], active=False))
        assert scope.security_exact_exceptions(path) == set()

        assert rejected(path, state(["apps/*/index.html"]))
        assert rejected(path, state(["../index.html"]))
        assert rejected(path, state(["shared/security.js"]))
        assert rejected(path, state(["runtime/security.js"]))
        assert rejected(path, state(["vendor/security.js"]))
        assert rejected(path, state(["README.md"]))
        assert rejected(path, state(["apps/not-a-workspace/index.html"]))
        assert rejected(path, state(["apps/pdf/io/file-open-controller.js"], gate="green"))

    print("Phase-scope security remediation contract: OK")


if __name__ == "__main__":
    main()
