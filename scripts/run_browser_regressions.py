#!/usr/bin/env python3
"""Run all Chromium/Playwright regression scripts in a stable order."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "tests" / "browser" / "results"
ALL_SCRIPTS = [
    # Run the heaviest multi-page scenario first. System Chromium can retain
    # short-lived helper processes between launches on constrained runners.
    "revalidate_cross_workspace_isolation.py",
    "revalidate_office_runtime_guards.py",
    "revalidate_hardening_controls.py",
    "revalidate_export_lifecycle_workspaces.py",
    "revalidate_unified_open_router.py",
    "revalidate_docx_three_eras.py",
    "revalidate_xlsx_three_eras.py",
    "revalidate_xls_zero_formula_display.py",
    "revalidate_pptx_three_eras.py",
    "revalidate_transactional_open_failures.py",
    "revalidate_launch_and_offline_modes.py",
]
GROUPS = {
    "package-security": [
        "revalidate_office_runtime_guards.py",
        "revalidate_hardening_controls.py",
    ],
    "lifecycle": [
        "revalidate_export_lifecycle_workspaces.py",
        "revalidate_unified_open_router.py",
        "revalidate_transactional_open_failures.py",
    ],
    "isolation-offline": [
        "revalidate_cross_workspace_isolation.py",
        "revalidate_launch_and_offline_modes.py",
    ],
    "documents-presentations": [
        "revalidate_docx_three_eras.py",
        "revalidate_pptx_three_eras.py",
    ],
    "spreadsheets": [
        "revalidate_xlsx_three_eras.py",
        "revalidate_xls_zero_formula_display.py",
    ],
}


def selected_scripts() -> tuple[str, list[str]]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("all", *GROUPS), default="all")
    args = parser.parse_args()
    return args.group, ALL_SCRIPTS if args.group == "all" else GROUPS[args.group]



def main() -> int:
    group, scripts = selected_scripts()
    RESULTS.mkdir(parents=True, exist_ok=True)
    records = []
    failed = False
    for name in scripts:
        path = ROOT / "tests" / "browser" / name
        print(f"[RUN ] {name}", flush=True)
        started = time.monotonic()
        try:
            completed = subprocess.run(
                [sys.executable, str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=120,
                check=False,
            )
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            timed_out = False
        except subprocess.TimeoutExpired as error:
            returncode = 124
            timed_out = True
            stdout = error.stdout.decode("utf-8", "replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
            stderr = error.stderr.decode("utf-8", "replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
            stderr = (stderr + "\nTimed out after 120 seconds.").strip()
        duration = round(time.monotonic() - started, 3)
        record = {
            "script": name,
            "passed": returncode == 0,
            "timed_out": timed_out,
            "duration_seconds": duration,
            "stdout_tail": stdout.strip().splitlines()[-20:],
            "stderr_tail": stderr.strip().splitlines()[-20:],
        }
        records.append(record)
        status = "PASS" if record["passed"] else "FAIL"
        print(f"[{status}] {name} ({duration:.3f}s)")
        if not record["passed"]:
            failed = True
            if stdout:
                print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)
    summary = {"group": group, "passed": sum(item["passed"] for item in records), "total": len(records), "records": records}
    (RESULTS / f"browser_regression_{group}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Browser regression summary: {summary['passed']}/{summary['total']} scripts passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
