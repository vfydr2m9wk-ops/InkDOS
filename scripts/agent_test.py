#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess

from agent_support import ROOT, command_for_test, matching_tests


def main():
    parser = argparse.ArgumentParser(
        description="Run focused InkDOS tests for one component."
    )
    parser.add_argument("component")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Include browser smoke tests, or all browser tests when used with --full.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the complete component test set instead of the default smoke gate.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List selected tests without executing them.",
    )
    args = parser.parse_args()

    tests = matching_tests(
        args.component,
        include_browser=args.browser,
        full=args.full,
    )
    if not tests:
        raise SystemExit(f"No focused tests found for component {args.component!r}")

    tier = "full" if args.full else "smoke"
    print(f"{tier.capitalize()} tests for {args.component}: {len(tests)}")
    for rel_path in tests:
        if not (ROOT / rel_path).is_file():
            raise SystemExit(f"Configured test is missing: {rel_path}")
        print(f"  {rel_path}")

    if args.list:
        return

    for rel_path in tests:
        print(f"\n==> {rel_path}", flush=True)
        subprocess.run(command_for_test(rel_path), cwd=ROOT, check=True)

    print(f"\nInkDOS {tier} component tests passed: {args.component}")


if __name__ == "__main__":
    main()
