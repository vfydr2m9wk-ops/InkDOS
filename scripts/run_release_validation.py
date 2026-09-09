#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
CMDS=[
 [sys.executable,'scripts/check_no_legacy_runtime.py'],
 [sys.executable,'scripts/build_txt_bundle.py','--check'],
 [sys.executable,'tests/test_csp_contract.py'],
 ['node','tests/test_pdf_p2_page_tools.cjs'],
 [sys.executable,'tests/test_doc_d1_contract.py'],
 [sys.executable,'tests/test_doc_d2_p1_contract.py'],
 [sys.executable,'tests/test_ppt_p1_structure_contract.py'],
 [sys.executable,'tests/test_ppt_p1_objects_contract.py'],
 [sys.executable,'scripts/validate_repository.py'],
 [sys.executable,'scripts/validate_app_isolation.py'],
 [sys.executable,'scripts/audit_source.py'],
 [sys.executable,'scripts/verify_checksums.py'],
 [sys.executable,'scripts/validate_suite_contracts.py'],
]
def main():
    for c in CMDS: subprocess.run(c,cwd=ROOT,check=True)
    print('InkDOS 2.0 clean-snapshot release validation passed.')
if __name__=='__main__': main()
