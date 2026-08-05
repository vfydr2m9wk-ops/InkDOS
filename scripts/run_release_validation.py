#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
commands=[[sys.executable,'scripts/generate_release_metadata.py'],[sys.executable,'scripts/check_no_legacy_runtime.py'],[sys.executable,'scripts/validate_repository.py'],[sys.executable,'scripts/audit_source.py'],[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],[sys.executable,'scripts/run_browser_regressions.py']]
for cmd in commands:
    print('+',' '.join(cmd)); subprocess.run(cmd,cwd=ROOT,check=True)
print('OK: release validation completed.')
