#!/usr/bin/env python3
"""Enforce functional-cycle or stability-audit scope against a Git base ref."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = {"documents", "spreadsheets", "presentations", "pdf", "txt", "epub"}
FUNCTIONAL_ROADMAP = [
    ("TXT-T1", "txt"),
    ("TXT-T2", "txt"),
    ("EPUB-E1", "epub"),
    ("EPUB-E2", "epub"),
    ("PDF-P1", "pdf"),
    ("PDF-P2", "pdf"),
    ("DOC-D1", "documents"),
    ("DOC-D2", "documents"),
    ("PPT-P1", "presentations"),
    ("PPT-P2", "presentations"),
    ("XLS-S1", "spreadsheets"),
    ("XLS-S2", "spreadsheets"),
    ("Audit", "cross-suite"),
    ("Freeze", "suite"),
]
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


def base_json_state(base_ref: str, filename: str) -> dict:
    try:
        raw = git("show", f"{base_ref}:{filename}")
    except subprocess.CalledProcessError:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def base_state(base_ref: str) -> dict:
    return base_json_state(base_ref, "STABILITY_STATE.json")


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
    if current == "cross-suite":
        candidate = state.get("freezeCandidate") or {}
        remediation = state.get("remediation") or {}
        if completed != order:
            raise SystemExit(
                "Cross-suite remediation requires every workspace to be completed in audit order; "
                f"expected completedWorkspaces={order}, got {completed}"
            )
        if candidate.get("status") != "superseded-by-user-device-remediation":
            raise SystemExit("Cross-suite remediation requires the prior freeze candidate to be superseded")
        if remediation.get("requiresCrossSuiteRevalidation") is not True:
            raise SystemExit("Cross-suite remediation requires requiresCrossSuiteRevalidation=true")
        return "stability:cross-suite", set(order)

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


def _functional_position(state: dict) -> tuple[int, str, str, set[str]]:
    if state.get("transitionGateRequired") is not True:
        raise SystemExit("FUNCTIONAL_STATE.json must require the transition architecture gate")
    current = state.get("currentPhase") or {}
    phase = current.get("id")
    workspace = current.get("workspace")
    if current.get("status") != "active":
        raise SystemExit("Invalid currentPhase/workspace in FUNCTIONAL_STATE.json")
    try:
        index = FUNCTIONAL_ROADMAP.index((phase, workspace))
    except ValueError as exc:
        raise SystemExit("Invalid currentPhase/workspace in FUNCTIONAL_STATE.json") from exc

    completed = state.get("completedPhases")
    expected_completed = [item[0] for item in FUNCTIONAL_ROADMAP[:index]]
    if completed != expected_completed:
        raise SystemExit(
            "FUNCTIONAL_STATE.json must advance sequentially; "
            f"expected completedPhases={expected_completed}, got {completed}"
        )

    expected_next = FUNCTIONAL_ROADMAP[index + 1] if index + 1 < len(FUNCTIONAL_ROADMAP) else None
    declared_next = state.get("nextPhase")
    if expected_next is not None:
        if not isinstance(declared_next, dict) or (declared_next.get("id"), declared_next.get("workspace")) != expected_next:
            raise SystemExit("FUNCTIONAL_STATE.json nextPhase does not match the canonical roadmap")
    elif declared_next not in (None, {}):
        raise SystemExit("Final functional phase must not declare another nextPhase")

    allowed = {workspace} if workspace in WORKSPACES else set()
    return index, phase, workspace, allowed


def functional_scope(path: Path, base_ref: str) -> tuple[str, set[str]]:
    if not path.is_file():
        raise SystemExit(f"Missing functional roadmap state: {path.name}")
    state = load_json(path)
    head_index, head_phase, _head_workspace, head_allowed = _functional_position(state)

    base = base_json_state(base_ref, path.name)
    if not base:
        return head_phase, head_allowed
    base_index, base_phase, _base_workspace, _base_allowed = _functional_position(base)

    if head_index < base_index:
        raise SystemExit("FUNCTIONAL_STATE.json cannot regress behind the integrated base")
    if head_index == base_index:
        return head_phase, head_allowed

    promoted = FUNCTIONAL_ROADMAP[base_index:head_index]
    promoted_apps = {workspace for _phase, workspace in promoted if workspace in WORKSPACES}
    if len(promoted_apps) > 1:
        raise SystemExit(
            "A single promotion cannot span functional changes in multiple workspaces; "
            f"promoted workspaces={sorted(promoted_apps)}"
        )
    label = promoted[0][0] if len(promoted) == 1 else f"{promoted[0][0]}→{promoted[-1][0]}"
    return label, promoted_apps


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
    phase, allowed_apps = scope or functional_scope(ROOT / args.state, args.base)
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

    apps = ", ".join(sorted(allowed_apps)) or "none"
    security_note = f"; explicit security exceptions: {len(security_allowed)}" if security_allowed else ""
    print(
        f"Phase-scope audit passed for {phase} ({mode}); {len(changed)} changed paths "
        f"inspected against {args.base}; allowed workspaces: {apps}{security_note}."
    )


if __name__ == "__main__":
    main()
