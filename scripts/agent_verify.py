#!/usr/bin/env python3
from __future__ import annotations

import argparse
from fnmatch import fnmatch
import subprocess
import sys

from agent_support import (
    ROOT,
    changed_paths,
    component,
    frozen_registry,
    is_owned_path,
)


def path_matches_rule(path: str, rule: str):
    if any(token in rule for token in "*?["):
        return fnmatch(path, rule)
    if rule.endswith("/"):
        return path.startswith(rule)
    return path == rule or path.startswith(rule.rstrip("/") + "/")


def main():
    parser = argparse.ArgumentParser(
        description="Verify InkDOS component scope, frozen legacy and focused tests."
    )
    parser.add_argument("component")
    parser.add_argument("--base", default="main")
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="PATH_OR_GLOB",
        help="Explicitly authorize an extra changed path/glob for this task.",
    )
    parser.add_argument(
        "--allow-frozen",
        action="append",
        default=[],
        metavar="ID",
        help="Explicitly authorize changes to one frozen-legacy entry.",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Include component browser tests.",
    )
    parser.add_argument(
        "--scope-only",
        action="store_true",
        help="Check scope/frozen legacy without running tests.",
    )
    args = parser.parse_args()

    component(args.component)
    changed = changed_paths(args.base)
    print(f"Changed paths against {args.base}: {len(changed)}")
    for path in changed:
        print(f"  {path}")

    violations = []
    for path in changed:
        if is_owned_path(args.component, path):
            continue
        if any(path_matches_rule(path, rule) for rule in args.allow):
            continue
        violations.append(path)

    if violations:
        rendered = "\n".join(f"  - {path}" for path in violations)
        raise SystemExit(
            "SCOPE VIOLATION\n"
            f"Target component: {args.component}\n"
            "Unexpected changed paths:\n"
            f"{rendered}\n"
            "Use --allow only when the task explicitly requires those paths."
        )

    frozen_hits = []
    authorized = set(args.allow_frozen)
    for entry in frozen_registry().get("entries", []):
        entry_id = entry["id"]
        if entry_id in authorized:
            continue
        rules = entry.get("paths", [])
        for path in changed:
            if any(path_matches_rule(path, rule) for rule in rules):
                frozen_hits.append((entry_id, path))

    if frozen_hits:
        rendered = "\n".join(
            f"  - {entry_id}: {path}" for entry_id, path in frozen_hits
        )
        raise SystemExit(
            "FROZEN LEGACY VIOLATION\n"
            f"{rendered}\n"
            "Use --allow-frozen <id> only when the task explicitly authorizes it."
        )

    print("Scope check: PASS")
    print("Frozen legacy check: PASS")

    if args.scope_only:
        return

    test_cmd = [sys.executable, "scripts/agent_test.py", args.component]
    if args.browser:
        test_cmd.append("--browser")
    subprocess.run(test_cmd, cwd=ROOT, check=True)

    subprocess.run(
        [sys.executable, "scripts/validate_app_isolation.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "tests/test_csp_contract.py"],
        cwd=ROOT,
        check=True,
    )
    print(f"InkDOS component verification passed: {args.component}")


if __name__ == "__main__":
    main()
