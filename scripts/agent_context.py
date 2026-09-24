#!/usr/bin/env python3
from __future__ import annotations

import argparse

from agent_support import component, frozen_registry, matching_tests, product_version


def main():
    parser = argparse.ArgumentParser(
        description="Print the minimum InkDOS context for one component."
    )
    parser.add_argument("component")
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Include browser tests in the displayed focused test set.",
    )
    args = parser.parse_args()

    cfg = component(args.component)
    frozen = [
        entry
        for entry in frozen_registry().get("entries", [])
        if args.component in entry.get("components", [])
    ]

    print("InkDOS agent context")
    print(f"Global version: {product_version()}")
    print(f"Component: {args.component} ({cfg['displayName']})")
    print(f"Root: {cfg['root']}")
    print(f"Entry: {cfg['entry']}")
    formats = ", ".join(cfg.get("formats", [])) or "none"
    print(f"Formats: {formats}")
    print()
    print("Normal owned scope:")
    for path in cfg.get("ownedPaths", []):
        print(f"  - {path}")
    for path in cfg.get("ownedPrefixes", []):
        print(f"  - {path}**")
    print("Regression-test scope:")
    for pattern in cfg.get("testGlobs", []):
        print(f"  - {pattern}")
    print()
    print("Focused tests:")
    tests = matching_tests(args.component, include_browser=args.browser)
    if tests:
        for path in tests:
            print(f"  - {path}")
    else:
        print("  - none discovered")
    print()
    print("Frozen legacy affecting this component:")
    if frozen:
        for entry in frozen:
            print(f"  - {entry['id']}: {entry.get('reason', '')}")
    else:
        print("  - none registered")
    print()
    print("Maintenance rules:")
    print("  - preserve working code")
    print("  - no opportunistic refactoring")
    print("  - do not modify sibling apps without explicit justification")
    print("  - do not rename stable APIs merely for cleanup")
    print("  - frozen legacy requires explicit authorization")
    print("  - use the smallest correct diff")
    print()
    print("Development gate:")
    print(f"  python scripts/agent_test.py {args.component}")
    print(f"  python scripts/agent_verify.py {args.component} --base main")


if __name__ == "__main__":
    main()
