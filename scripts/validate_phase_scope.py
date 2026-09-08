#!/usr/bin/env python3
"""Enforce functional-cycle or stability-audit scope against a Git base ref."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = {"documents", "spreadsheets", "presentations", "pdf", "txt", "epub"}
GLOBAL_ALLOWED_EXACT = {
    "FUNCTIONAL_STATE.json",
    "STABILITY_STATE.json",
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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def stability_scope(path: Path) -> tuple[str, set[str]] | None:
    if not path.is_file():
        return None
    state = load_json(path)
    if state.get("active") is not True:
        return None
    if state.get("program") != "stability-functional-isolation":
        raise SystemExit("Invalid active stability program")
    order = [item for item in state.get("auditOrder", []) if item in WORKSPACES]
    current = state.get("currentWorkspace")
    completed = state.get("completedWorkspaces", [])
    if current not in WORKSPACES or current not in order:
        raise SystemExit("Invalid currentWorkspace in STABILITY_STATE.json")
    if any(item not in WORKSPACES for item in completed) or len(completed) != len(set(completed)):
        raise SystemExit("Invalid completedWorkspaces in STABILITY_STATE.json")
    current_index = order.index(current)
    expected_completed = order[:current_index]
    if completed != expected_completed:
        raise SystemExit(
            "STABILITY_STATE.json must advance sequentially; "
            f"expected completedWorkspaces={expected_completed}, got {completed}"
        )
    return f"stability:{current}", set(completed) | {current}


def functional_scope(path: Path) -> tuple[str, set[str]]:
    if not path.is_file():
        raise SystemExit(f"Missing functional roadmap state: {path.name}")
    state = load_json(path)
    if state.get("transitionGateRequired") is not True:
        raise SystemExit("FUNCTIONAL_STATE.json must require the transition architecture gate")
    current = state.get("currentPhase") or {}
    workspace = current.get("workspace")
    phase = current.get("id")
    if workspace not in WORKSPACES or not phase:
        raise SystemExit("Invalid currentPhase/workspace in FUNCTIONAL_STATE.json")
    return phase, {workspace}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main", help="Git base ref used for the phase diff")
    parser.add_argument("--state", default="FUNCTIONAL_STATE.json")
    parser.add_argument("--stability-state", default="STABILITY_STATE.json")
    args = parser.parse_args()

    scope = stability_scope(ROOT / args.stability_state)
    mode = "stability" if scope else "functional"
    phase, allowed_apps = scope or functional_scope(ROOT / args.state)

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
            if app not in allowed_apps:
                label = "Unopened workspace changed during stability audit" if mode == "stability" else "Sibling workspace changed"
                violations.append(f"{label} during {phase}: {path}")
            continue
        if path in GLOBAL_ALLOWED_EXACT or path.startswith(GLOBAL_ALLOWED_PREFIXES):
            continue
        violations.append(f"Path is outside the phase allowlist: {path}")

    if violations:
        print(f"Phase-scope audit FAILED for {phase} ({mode}).")
        for item in violations:
            print(f" - {item}")
        raise SystemExit(1)

    apps = ", ".join(sorted(allowed_apps))
    print(
        f"Phase-scope audit passed for {phase} ({mode}); {len(changed)} changed paths "
        f"inspected against {args.base}; allowed workspaces: {apps}."
    )


if __name__ == "__main__":
    main()
