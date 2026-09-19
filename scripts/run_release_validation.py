#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CMDS = [
    [sys.executable, "scripts/check_no_legacy_runtime.py"],
    [sys.executable, "scripts/build_txt_bundle.py", "--check"],
    [sys.executable, "tests/test_csp_contract.py"],
    ["node", "tests/test_pdf_p2_page_tools.cjs"],
    [sys.executable, "tests/test_doc_d1_contract.py"],
    [sys.executable, "tests/test_doc_d2_p1_contract.py"],
    [sys.executable, "tests/test_documents_243_insert_table_cancel_contract.py"],
    [sys.executable, "tests/test_documents_243_interaction_contract.py"],
    [sys.executable, "tests/test_home_density_layout_contract.py"],
    [sys.executable, "tests/test_ppt_p1_structure_contract.py"],
    [sys.executable, "tests/test_ppt_p1_objects_contract.py"],
    [sys.executable, "tests/test_epub_webkit_deflate_contract.py"],
    [sys.executable, "tests/test_txt_format_expansion_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_text_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_encoding_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_save_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_conversion_guard_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_formula_paste_guard_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_edit_preservation_contract.py"],
    [sys.executable, "tests/test_tauri_goal3_workspace_contract.py"],
    [sys.executable, "tests/test_tauri_goal3_native_window_contract.py"],
    [sys.executable, "tests/test_localization_settings_contract.py"],
    [sys.executable, "tests/test_localization_completeness_contract.py"],
    [sys.executable, "tests/test_desktop_ux_contract.py"],
    [sys.executable, "tests/test_app_isolation_shared_density_contract.py"],
    [sys.executable, "tests/test_release_pipeline_contract.py"],
    [sys.executable, "tests/test_repository_privacy_contract.py"],
    [sys.executable, "scripts/validate_repository.py"],
    [sys.executable, "scripts/validate_app_isolation.py"],
    [sys.executable, "scripts/audit_source.py"],
    [sys.executable, "scripts/validate_suite_contracts.py"],
]


def main():
    for command in CMDS:
        subprocess.run(command, cwd=ROOT, check=True)
    print("InkDOS clean-snapshot release validation passed.")


if __name__ == "__main__":
    main()
