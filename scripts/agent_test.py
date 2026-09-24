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
        help="Also run tests whose filenames contain _browser.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List selected tests without executing them.",
    )
    args = parser.parse_args()

    tests = matching_tests(args.component, include_browser=args.browser)
    if not tests:
        raise SystemExit(f"No focused tests found for component {args.component!r}")

    print(f"Focused tests for {args.component}: {len(tests)}")
    for rel_path in tests:
        print(f"  {rel_path}")

    if args.list:
        return

    for rel_path in tests:
        print(f"\n==> {rel_path}", flush=True)
        subprocess.run(command_for_test(rel_path), cwd=ROOT, check=True)

    print(f"\nInkDOS focused component tests passed: {args.component}")


if __name__ == "__main__":
    main()
