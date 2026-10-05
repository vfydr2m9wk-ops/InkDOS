#!/usr/bin/env python3
"""Run test files that only define ``test_*`` functions (no ``__main__`` block).

Such files exit 0 without testing anything when executed as ``python tests/x.py``. This runner
imports each one and calls its ``test_*`` functions in definition order, with no pytest
dependency. Without arguments it discovers every ``tests/test_*.py`` that has no ``__main__``
block, so new function-style tests are covered automatically.
"""
from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def discover() -> list[Path]:
    return sorted(p for p in (ROOT / "tests").glob("test_*.py") if "__main__" not in p.read_text(encoding="utf-8"))


def run_file(path: Path) -> list[str]:
    spec = importlib.util.spec_from_file_location(f"inkdos_function_test_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return [f"{path.name}: import failed\n{traceback.format_exc()}"]
    tests = [(name, fn) for name, fn in vars(module).items()
             if name.startswith("test_") and inspect.isfunction(fn) and fn.__module__ == module.__name__]
    # no test_* functions: a script-style file whose module-level checks already ran on import
    failures = []
    for name, fn in sorted(tests, key=lambda item: item[1].__code__.co_firstlineno):
        try:
            fn()
        except Exception:
            failures.append(f"{path.name}::{name}\n{traceback.format_exc()}")
    return failures


def main(argv: list[str]) -> int:
    files = [Path(a).resolve() for a in argv] if argv else discover()
    if not files:
        print("No function-style test files found.")
        return 0
    failures: list[str] = []
    for path in files:
        failures += run_file(path)
    if failures:
        print("\n".join(failures), file=sys.stderr)
        print(f"{len(failures)} function-style test failure(s) in {len(files)} file(s).", file=sys.stderr)
        return 1
    print(f"Function-style tests passed: {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
