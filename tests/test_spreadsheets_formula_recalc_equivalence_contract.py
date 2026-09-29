#!/usr/bin/env python3
"""Regression: dependency-driven formula recalculation matches whole-workbook recalculation.

Runs tests/spreadsheets_formula_recalc_equivalence.cjs (random workbooks and edits, compared with the previous
evaluator that recalculated every formula four times) and checks that an edit recalculates only dependents.
"""
from __future__ import annotations
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_recalculation_equivalence():
    run = subprocess.run(["node", str(ROOT / "tests/spreadsheets_formula_recalc_equivalence.cjs")], capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "equivalence: OK" in run.stdout, run.stdout


if __name__ == "__main__":
    test_recalculation_equivalence()
    print("Spreadsheets formula recalculation equivalence contract: OK")
