#!/usr/bin/env python3
"""Run the release gate against a Library/export snapshot without mutating it.

The repository privacy contract intentionally relies on git metadata. Library exports do
not contain .git, so this wrapper creates an isolated temporary repository containing the
exact exported tree and runs the normal aggregate validation there. This validates the
current-tree privacy rules but does not claim validation of GitHub history.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    if (ROOT / ".git").exists():
        raise SystemExit("Export validation must run from a snapshot without .git metadata.")

    with tempfile.TemporaryDirectory(prefix="inkdos-export-validation-") as tmp:
        checkout = Path(tmp) / "InkDOS"
        shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        run(["git", "init", "-q"], checkout)
        synthetic_email = "inkdos-export-validation" + "@" + "invalid.local"
        run(["git", "config", "user.email", synthetic_email], checkout)
        run(["git", "config", "user.name", "InkDOS Export Validation"], checkout)
        run(["git", "add", "-A"], checkout)
        run(["git", "commit", "-qm", "synthetic export validation snapshot"], checkout)
        run([sys.executable, "scripts/run_release_validation.py"], checkout)

    print("InkDOS Library/export aggregate validation passed (current tree only; GitHub history not validated).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
