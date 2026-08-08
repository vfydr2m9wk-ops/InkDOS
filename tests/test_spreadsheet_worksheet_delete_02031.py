from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_delete_control_and_safety_contract_are_wired():
    tabs = (ROOT / "apps/spreadsheets/worksheet-tabs.js").read_text(encoding="utf-8")
    app = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
    styles = (ROOT / "apps/spreadsheets/styles.css").read_text(encoding="utf-8")
    assert "deleteSheetBtn" in tabs
    assert "Delete active worksheet" in tabs
    assert "canDelete" in tabs and "onDelete" in tabs
    assert "A workbook must keep at least one visible worksheet." in app
    assert "This cannot be undone." in app
    assert "formula drafts before deleting a worksheet" in app
    assert "#deleteSheetBtn" in styles


def test_xlsx_writer_reconciles_deleted_worksheets_without_rebuilding_package():
    package = (ROOT / "apps/spreadsheets/worksheet-package.js").read_text(encoding="utf-8")
    engine = (ROOT / "apps/spreadsheets/xlsx-engine.js").read_text(encoding="utf-8")
    assert "removeDeletedSheets" in package
    assert "keptPaths" in package
    assert "localSheetId" in package
    assert "calcChain" in package
    assert "syncSheets(zip,book" in engine
    assert "removeDeletedSheets" in package and "appendNewSheets" in package


def test_recovery_matches_surviving_sheet_by_stable_package_identity():
    app = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
    assert "baseSheets.find(item=>item.path===metadata.path)" in app
    assert "baseSheets.find(item=>item.name===metadata.name)" in app
