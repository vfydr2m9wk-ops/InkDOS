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
    [sys.executable, "tests/test_spreadsheets_delimited_plaintext_paste_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_semantic_paste_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_fill_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_numeric_operation_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_xlsx_numeric_text_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_xlsx_formula_cache_type_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_xls_formula_cache_type_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_formula_aggregate_finite_result_contract.py"],
    [sys.executable, "tests/test_spreadsheets_formula_arithmetic_type_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_formula_if_error_propagation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_formula_if_condition_type_contract.py"],
    [sys.executable, "tests/test_spreadsheets_hide_zero_type_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_numeric_operation_prompt_cancel_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_formula_engine_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_engine_xlsx_only_guard_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_structure_type_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_delimited_clear_history_type_preservation_contract.py"],
    [sys.executable, "tests/test_spreadsheets_selection_stats_type_preservation_contract.py"],
    [sys.executable, "tests/test_tauri_goal3_workspace_contract.py"],
    [sys.executable, "tests/test_tauri_goal3_native_window_contract.py"],
    [sys.executable, "tests/test_localization_settings_contract.py"],
    [sys.executable, "tests/test_localization_completeness_contract.py"],
    [sys.executable, "tests/test_desktop_ux_contract.py"],
    [sys.executable, "tests/test_app_isolation_shared_density_contract.py"],
    [sys.executable, "tests/test_release_pipeline_contract.py"],
    [sys.executable, "tests/test_243_release_version_agnostic_contract.py"],
    [sys.executable, "tests/test_243_updater_manifest_dry_run_contract.py"],
    [sys.executable, "tests/test_243_upgrade_gate_contract.py"],
    [sys.executable, "tests/test_243_final_version_consistency_harness.py"],
    [sys.executable, "tests/test_243_release_inventory_contract.py"],
    [sys.executable, "tests/test_243_release_bundle_coherence_contract.py"],
    [sys.executable, "tests/test_243_publication_transaction_contract.py"],
    [sys.executable, "tests/test_243_release_authorization_contract.py"],
    [sys.executable, "tests/test_243_windows_evidence_collector_contract.py"],
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
