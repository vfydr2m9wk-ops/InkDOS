#!/usr/bin/env python3
"""Run the InkDOS browser suite across installed Playwright engines.

The normal update workflow stays fast by running Chromium only. This explicit
matrix command runs Chromium, Firefox, and WebKit when their Playwright browser
binaries are installed. Set INKDOS_BROWSER_MATRIX_STRICT=1 to fail when an
engine is unavailable.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "tests" / "browser" / "results"
DEFAULT_BROWSERS = ("chromium", "firefox", "webkit")


def installed(name: str) -> bool:
    script = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path('tests/browser').resolve()))
from playwright.sync_api import sync_playwright
from browser_support import browser_is_installed
with sync_playwright() as p:
    raise SystemExit(0 if browser_is_installed(p, sys.argv[1]) else 1)
"""
    return subprocess.run([sys.executable, "-c", script, name], cwd=ROOT).returncode == 0


def main() -> int:
    requested = tuple(x.strip().lower() for x in os.environ.get("INKDOS_BROWSERS", ",".join(DEFAULT_BROWSERS)).split(",") if x.strip())
    strict = os.environ.get("INKDOS_BROWSER_MATRIX_STRICT", "0") == "1"
    invalid = [name for name in requested if name not in DEFAULT_BROWSERS]
    if invalid:
        print(f"Unsupported browser engine(s): {', '.join(invalid)}", file=sys.stderr)
        return 2
    RESULTS.mkdir(parents=True, exist_ok=True)
    records = []
    failed = False
    for name in requested:
        available = installed(name)
        if not available:
            records.append({"browser": name, "status": "missing", "passed": False if strict else None})
            print(f"[SKIP] {name}: Playwright browser binary is not installed.")
            if strict:
                failed = True
            continue
        print(f"[RUN ] Browser matrix: {name}", flush=True)
        env = os.environ.copy()
        env["INKDOS_BROWSER"] = name
        started = time.monotonic()
        result = subprocess.run([sys.executable, "scripts/run_browser_regressions.py"], cwd=ROOT, env=env)
        duration = round(time.monotonic() - started, 3)
        records.append({"browser": name, "status": "passed" if result.returncode == 0 else "failed", "passed": result.returncode == 0, "duration_seconds": duration})
        if result.returncode:
            failed = True
    summary = {"strict": strict, "requested": list(requested), "records": records, "passed": not failed}
    (RESULTS / "browser_matrix_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
