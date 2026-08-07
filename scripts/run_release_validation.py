#!/usr/bin/env python3
"""Run the complete reproducible release-validation cycle once."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    ("Repository validation", [sys.executable, "scripts/validate_repository.py"]),
    ("Source audit", [sys.executable, "scripts/audit_source.py"]),
    ("Architecture guardrails", [sys.executable, "scripts/check_architecture_guardrails.py"]),
    ("Unit and package tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]),
    ("Browser regressions", [sys.executable, "scripts/run_browser_regressions.py"]),
    ("Checksum verification", [sys.executable, "scripts/verify_checksums.py"]),
]


def main() -> int:
    started = time.monotonic()
    for label, command in COMMANDS:
        print(f"\n=== {label} ===", flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            print(f"Release-validation cycle failed during: {label}", file=sys.stderr)
            return result.returncode
    duration = time.monotonic() - started
    print(f"\nRelease-validation cycle passed in {duration:.1f} seconds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
