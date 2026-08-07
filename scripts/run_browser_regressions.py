#!/usr/bin/env python3
"""Run all Playwright regression scripts for the selected browser engine."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "tests" / "browser" / "results"
SCRIPTS = [
    "revalidate_office_runtime_guards.py",
    "revalidate_docx_three_eras.py",
    "revalidate_xlsx_three_eras.py",
    "revalidate_xls_zero_formula_display.py",
    "revalidate_pptx_three_eras.py",
    "revalidate_transactional_open_failures.py",
    "revalidate_cross_workspace_isolation.py",
    "revalidate_launch_and_offline_modes.py",
    "revalidate_v0201_consistency.py",
    "revalidate_v0202_local_recovery.py",
    "revalidate_presentations_controls.py",
    "revalidate_presentations_slideshow.py",
    "revalidate_pdf_page_rendering.py",
    "revalidate_pdf_navigation.py",
    "revalidate_pdf_review.py",
    "revalidate_v02021_functional_corrections.py",
]


def main() -> int:
    browser_name = os.environ.get("INKDESK_BROWSER", "chromium").strip().lower()
    RESULTS.mkdir(parents=True, exist_ok=True)
    records = []
    failed = False
    for name in SCRIPTS:
        path = ROOT / "tests" / "browser" / name
        print(f"[RUN ] {browser_name}: {name}", flush=True)
        started = time.monotonic()
        log_base = RESULTS / f".{Path(name).stem}"
        stdout_path = log_base.with_suffix(".stdout.log")
        stderr_path = log_base.with_suffix(".stderr.log")
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
            process = subprocess.Popen(
                [sys.executable, str(path)],
                cwd=ROOT,
                text=True,
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True,
            )
            try:
                returncode = process.wait(timeout=90)
                timed_out = False
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
                returncode = 124
                timed_out = True
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
        stdout_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)
        if timed_out:
            stderr = (stderr + "\nTimed out after 90 seconds.").strip()
        duration = round(time.monotonic() - started, 3)
        record = {
            "browser": browser_name,
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
    summary = {"browser": browser_name, "passed": sum(item["passed"] for item in records), "total": len(records), "records": records}
    (RESULTS / f"browser_regression_summary_{browser_name}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Browser regression summary: {summary['passed']}/{summary['total']} scripts passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
