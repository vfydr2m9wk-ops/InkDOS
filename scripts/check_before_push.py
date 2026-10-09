#!/usr/bin/env python3
"""What to run before every push (about two minutes): regenerate the generated files, then the same release
validation the CI runs first, then the UI smoke check (scripts/smoke_ui.py, Chromium set up like an iPad).

    python3 scripts/check_before_push.py            # stops at the first failure
    python3 scripts/check_before_push.py --full     # also every browser test listed in .github/workflows/ci.yml
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
STEPS = [
    ('Plain Text bundle', [PY, 'scripts/build_txt_bundle.py']),
    ('offline snapshot', [PY, 'scripts/build_offline_snapshot.py']),
    ('release validation (CI)', [PY, 'scripts/run_release_validation.py']),
    ('UI smoke (iPad-like Chromium)', [PY, 'scripts/smoke_ui.py', '--out', 'smoke-out']),
]


def run(name, cmd):
    print(f'== {name}', flush=True)
    result = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode:
        print(result.stdout[-4000:])
        sys.exit(f'FAILED: {name}')
    print('   ok', flush=True)


def main():
    for name, cmd in STEPS:
        run(name, cmd)
    if '--full' in sys.argv:
        ci = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
        for test in re.findall(r'run: python (tests/\w+\.py)', ci):
            run(test, [PY, test])
    changed = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True).stdout
    if changed.strip():
        print('Generated files changed; commit them with the change:\n' + changed)
    print('All checks passed.')


if __name__ == '__main__':
    main()
