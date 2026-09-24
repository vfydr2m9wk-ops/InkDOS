#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "artifacts" / "behavioral-stability"
REPORT = REPORT_DIR / "report.json"

TESTS = (
    "tests/test_cross_suite_stateful_soak_browser.py",
    "tests/test_documents_stability_browser.py",
    "tests/test_doc_d1_roundtrip.py",
    "tests/test_spreadsheets_stability_browser.py",
    "tests/test_presentations_stability_browser.py",
    "tests/test_ppt_p1_structure_roundtrip.py",
    "tests/test_epub_stability_browser.py",
    "tests/test_pdf_stability_roundtrip.py",
)


def tail(value: str, lines: int = 80) -> str:
    parts = value.splitlines()
    return "\n".join(parts[-lines:])


def main() -> None:
    browser = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser not in {"chromium", "firefox", "webkit"}:
        raise SystemExit(f"Unsupported BROWSER={browser}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "browser": browser,
        "statefulCycles": int(os.environ.get("INKDOS_STATEFUL_CYCLES", "3")),
        "tests": [],
        "passed": False,
    }

    env = os.environ.copy()
    env["BROWSER"] = browser

    for rel in TESTS:
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"Behavioral stability test is missing: {rel}")

        command = [sys.executable, rel]
        replay = f"BROWSER={browser} python {rel}"
        if rel.endswith("test_cross_suite_stateful_soak_browser.py"):
            replay = (
                f"BROWSER={browser} "
                f"INKDOS_STATEFUL_CYCLES={env.get('INKDOS_STATEFUL_CYCLES', '3')} "
                f"python {rel}"
            )

        started = time.monotonic()
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        elapsed = round(time.monotonic() - started, 3)

        entry = {
            "test": rel,
            "returncode": completed.returncode,
            "durationSeconds": elapsed,
            "replay": replay,
            "stdoutTail": tail(completed.stdout),
            "stderrTail": tail(completed.stderr),
        }
        report["tests"].append(entry)
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        status = "PASS" if completed.returncode == 0 else "FAIL"
        print(f"[{status}] {rel} ({elapsed:.3f}s)", flush=True)
        if completed.returncode != 0:
            print(f"REPLAY: {replay}", file=sys.stderr)
            if completed.stdout:
                print(completed.stdout, file=sys.stderr)
            if completed.stderr:
                print(completed.stderr, file=sys.stderr)
            raise SystemExit(completed.returncode)

    report["passed"] = True
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Behavioral stability gate passed: {len(TESTS)} tests")
    print(f"Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
