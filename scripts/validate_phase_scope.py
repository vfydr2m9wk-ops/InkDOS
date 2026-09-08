#!/usr/bin/env python3
"""Enforce one-workspace-per-functional-cycle against a Git base ref."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = {"documents", "spreadsheets", "presentations", "pdf", "txt", "epub"}
GLOBAL_ALLOWED_EXACT = {
    "FUNCTIONAL_STATE.json",
    "CHECKSUMS.sha256",
    "SOURCE_LOCK.json",
    "BUILD_INFO.json",
    "SOURCE_MANIFEST.json",
    "RELEASE_MANIFEST.json",
    "service-worker.js",
    "requirements-ci.txt",
}
GLOBAL_ALLOWED_PREFIXES = (
    ".github/workflows/",
    "docs/",
    "scripts/",
    "tests/",
)
HOME_FROZEN_EXACT = {"index.html", "manifest.webmanifest"}
HOME_FROZEN_PREFIXES = ("assets/",)
FORBIDDEN_SHARED_PREFIXES = ("shared/", "runtime/", "vendor/")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main", help="Git base ref used for the phase diff")
    parser.add_argument("--state", default="FUNCTIONAL_STATE.json")
    args = parser.parse_args()

    state_path = ROOT / args.state
    if not state_path.is_file():
        raise SystemExit(f"Missing functional roadmap state: {args.state}")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("transitionGateRequired") is not True:
        raise SystemExit("FUNCTIONAL_STATE.json must require the transition architecture gate")
    current = state.get("currentPhase") or {}
    workspace = current.get("workspace")
    phase = current.get("id")
    if workspace not in WORKSPACES or not phase:
        raise SystemExit("Invalid currentPhase/workspace in FUNCTIONAL_STATE.json")

    try:
        git("rev-parse", "--verify", args.base)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Base ref is unavailable: {args.base}") from exc

    changed = [p for p in git("diff", "--name-only", "--diff-filter=ACMRD", f"{args.base}...HEAD").splitlines() if p]
    violations: list[str] = []

    for path in changed:
        if path in HOME_FROZEN_EXACT or path.startswith(HOME_FROZEN_PREFIXES):
            violations.append(f"Home is frozen during {phase}: {path}")
            continue
        if path.startswith(FORBIDDEN_SHARED_PREFIXES):
            violations.append(f"Shared functional/runtime root is forbidden: {path}")
            continue
        if path.startswith("apps/"):
            parts = path.split("/", 2)
            app = parts[1] if len(parts) > 1 else ""
            if app != workspace:
                violations.append(f"Sibling workspace changed during {phase}: {path}")
            continue
        if path in GLOBAL_ALLOWED_EXACT or path.startswith(GLOBAL_ALLOWED_PREFIXES):
            continue
        violations.append(f"Path is outside the phase allowlist: {path}")

    if violations:
        print(f"Phase-scope audit FAILED for {phase} ({workspace}).")
        for item in violations:
            print(f" - {item}")
        raise SystemExit(1)

    print(f"Phase-scope audit passed for {phase} ({workspace}); {len(changed)} changed paths inspected against {args.base}.")


if __name__ == "__main__":
    main()
