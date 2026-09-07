#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
CMDS=[
 [sys.executable,'scripts/check_no_legacy_runtime.py'],
 [sys.executable,'scripts/validate_repository.py'],
 [sys.executable,'scripts/audit_source.py'],
 [sys.executable,'scripts/verify_checksums.py'],
 [sys.executable,'scripts/validate_suite_contracts.py'],
]
def main():
    for c in CMDS: subprocess.run(c,cwd=ROOT,check=True)
    print('InkDOS 2.0 clean-snapshot release validation passed.')
if __name__=='__main__': main()
