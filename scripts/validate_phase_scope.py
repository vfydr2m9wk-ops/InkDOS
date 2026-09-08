#!/usr/bin/env python3
"""Enforce functional-cycle or stability-audit scope against a Git base ref."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = {"documents", "spreadsheets", "presentations", "pdf", "txt", "epub"}
GLOBAL_ALLOWED_EXACT = {
    "FUNCTIONAL_STATE.json",
    "STABILITY_STATE.json",
    "SECURITY_REMEDIATION_STATE.json",
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


def frozen_anchor(state: dict) -> str | None:
    if state.get("program") != "stability-functional-isolation":
        return None
    if state.get("active") is not False or state.get("currentWorkspace") != "freeze":
        return None
    frozen = state.get("freezeCandidate") or {}
    if frozen.get("status") != "frozen":
        return None
    anchor = frozen.get("runtimeAnchor")
    return anchor if isinstance(anchor, str) and anchor else None


def base_state(base_ref: str) -> dict:
    try:
        raw = git("show", f"{base_ref}:STABILITY_STATE.json")
    except subprocess.CalledProcessError:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def stability_scope(path: Path, base_ref: str) -> tuple[str, set[str]] | None:
    if not path.is_file():
        return None
    state = load_json(path)
    active = state.get("active")
    program = state.get("program")
    if program != "stability-functional-isolation":
        if active is True:
            raise SystemExit("Invalid active stability program")
        return None

    order = [item for item in state.get("auditOrder", []) if item in WORKSPACES]
    completed = state.get("completedWorkspaces", [])
    if any(item not in WORKSPACES for item in completed) or len(completed) != len(set(completed)):
        raise SystemExit("Invalid completedWorkspaces in STABILITY_STATE.json")

    # A completed stability program governs only the PR that is promoting that
    # frozen baseline into the selected base. Once the same runtime anchor is
    # already present in base, normal future development falls back to
    # FUNCTIONAL_STATE.json and the one-workspace rule becomes authoritative again.
    if active is False and state.get("currentWorkspace") == "freeze":
        anchor = frozen_anchor(state)
        if not anchor:
            raise SystemExit("Inactive stability freeze must have status=frozen and a runtimeAnchor")
        if set(order) != WORKSPACES or len(order) != len(WORKSPACES):
            raise SystemExit("Frozen stability auditOrder must contain all six workspaces exactly once")
        if completed != order:
            raise SystemExit(
                "Frozen STABILITY_STATE.json must list every audited workspace in order; "
                f"expected completedWorkspaces={order}, got {completed}"
            )
        if frozen_anchor(base_state(base_ref)) == anchor:
            return None
        return "stability:freeze", set(order)

    if active is not True:
        return None

    current = state.get("currentWorkspace")
    if current not in WORKSPACES or current not in order:
        raise SystemExit("Invalid currentWorkspace in STABILITY_STATE.json")
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


def security_exact_exceptions(path: Path) -> set[str]:
    """Return narrowly declared security exceptions without weakening shared-root rules."""
    if not path.is_file():
        return set()
    state = load_json(path)
    if state.get("program") != "security-remediation":
        if state.get("active") is True:
            raise SystemExit("Invalid active security remediation program")
        return set()
    if state.get("active") is not True:
        return set()
    if state.get("securityGate") != "blocked":
        raise SystemExit("Active security remediation requires securityGate=blocked")
    if state.get("scopePolicy") != "functional-plus-explicit-security-exceptions":
        raise SystemExit("Invalid security remediation scopePolicy")

    raw_paths = state.get("allowedExactPaths")
    rationale = state.get("rationale")
    if not isinstance(raw_paths, list) or not isinstance(rationale, dict):
        raise SystemExit("Security remediation requires allowedExactPaths and rationale")
    if len(raw_paths) != len(set(raw_paths)):
        raise SystemExit("Duplicate path in security remediation allowlist")

    allowed: set[str] = set()
    for item in raw_paths:
        if not isinstance(item, str) or not item or "*" in item or "?" in item or "[" in item:
            raise SystemExit(f"Security remediation path must be exact: {item!r}")
        posix = PurePosixPath(item)
        if posix.is_absolute() or ".." in posix.parts or item.endswith("/"):
            raise SystemExit(f"Unsafe security remediation path: {item}")
        if item.startswith(FORBIDDEN_SHARED_PREFIXES):
            raise SystemExit(f"Security remediation cannot override forbidden shared root: {item}")
        if not (item in HOME_FROZEN_EXACT or item.startswith("apps/")):
            raise SystemExit(f"Security exception must target a frozen Home entry or app-local path: {item}")
        parts = item.split("/", 2)
        if item.startswith("apps/") and (len(parts) < 3 or parts[1] not in WORKSPACES):
            raise SystemExit(f"Unknown workspace in security remediation path: {item}")
        reason = rationale.get(item)
        if not isinstance(reason, str) or not reason.strip():
            raise SystemExit(f"Missing rationale for security remediation path: {item}")
        allowed.add(item)
    return allowed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main", help="Git base ref used for the phase diff")
    parser.add_argument("--state", default="FUNCTIONAL_STATE.json")
    parser.add_argument("--stability-state", default="STABILITY_STATE.json")
    parser.add_argument("--security-state", default="SECURITY_REMEDIATION_STATE.json")
    args = parser.parse_args()

    try:
        git("rev-parse", "--verify", args.base)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Base ref is unavailable: {args.base}") from exc

    scope = stability_scope(ROOT / args.stability_state, args.base)
    mode = "stability" if scope else "functional"
    phase, allowed_apps = scope or functional_scope(ROOT / args.state)
    security_allowed = security_exact_exceptions(ROOT / args.security_state)

    changed = [p for p in git("diff", "--name-only", "--diff-filter=ACMRD", f"{args.base}...HEAD").splitlines() if p]
    violations: list[str] = []

    for path in changed:
        if path in HOME_FROZEN_EXACT or path.startswith(HOME_FROZEN_PREFIXES):
            if path in security_allowed:
                continue
            violations.append(f"Home is frozen during {phase}: {path}")
            continue
        if path.startswith(FORBIDDEN_SHARED_PREFIXES):
            violations.append(f"Shared functional/runtime root is forbidden: {path}")
            continue
        if path.startswith("apps/"):
            parts = path.split("/", 2)
            app = parts[1] if len(parts) > 1 else ""
            if app not in allowed_apps and path not in security_allowed:
                label = "Unopened workspace changed during stability audit" if mode == "stability" else "Sibling workspace changed"
                violations.append(f"{label} during {phase}: {path}")
            continue
        if path in GLOBAL_ALLOWED_EXACT or path.startswith(GLOBAL_ALLOWED_PREFIXES):
            continue
        if path in security_allowed:
            continue
        violations.append(f"Path is outside the phase allowlist: {path}")

    if violations:
        print(f"Phase-scope audit FAILED for {phase} ({mode}).")
        for item in violations:
            print(f" - {item}")
        raise SystemExit(1)

    apps = ", ".join(sorted(allowed_apps))
    security_note = f"; explicit security exceptions: {len(security_allowed)}" if security_allowed else ""
    print(
        f"Phase-scope audit passed for {phase} ({mode}); {len(changed)} changed paths "
        f"inspected against {args.base}; allowed workspaces: {apps}{security_note}."
    )


if __name__ == "__main__":
    main()
