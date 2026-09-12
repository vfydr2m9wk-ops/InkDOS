#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = {
    "documents": "Documents",
    "epub": "EPUB Reader",
    "pdf": "PDF Workspace",
    "presentations": "Presentations",
    "spreadsheets": "Spreadsheets",
    "txt": "Text Editor",
}


def main() -> None:
    for app, title in APPS.items():
        app_root = ROOT / "apps" / app
        help_file = app_root / "help" / "help.js"
        app_file = app_root / "app.js"

        assert help_file.is_file(), f"{app}: app-local help/help.js is required"
        assert app_file.is_file(), f"{app}: app.js is required"

        help_source = help_file.read_text(encoding="utf-8")
        app_source = app_file.read_text(encoding="utf-8")

        assert "help/help.js" in app_source, f"{app}: app.js must load its own help module"
        assert "optionalHelp" in app_source, f"{app}: Help must be loaded as an optional module"
        assert "data-inkdos-help-entry" in help_source, f"{app}: Help menu entry marker missing"
        assert 'data-icon="CircleHelp"' in help_source, f"{app}: CircleHelp icon marker missing"
        assert ">Help</span>" in help_source, f"{app}: Help label missing"
        assert "data-inkdos-help-dialog" in help_source, f"{app}: Help dialog marker missing"
        assert title in help_source, f"{app}: Help content must be app-specific"

        # App Help must remain app-local: no cross-app imports or shared Help dependency.
        assert "../../apps/" not in help_source, f"{app}: Help may not depend on another app"
        assert "../documents/" not in help_source
        assert "../epub/" not in help_source
        assert "../pdf/" not in help_source
        assert "../presentations/" not in help_source
        assert "../spreadsheets/" not in help_source
        assert "../txt/" not in help_source

    sheet_help = (ROOT / "apps" / "spreadsheets" / "help" / "help.js").read_text(encoding="utf-8")
    for function_name in ("SUM", "AVERAGE", "MIN", "MAX", "COUNT", "PRODUCT", "IF"):
        assert function_name in sheet_help, f"Spreadsheets Help must document {function_name}"
    assert "=SUM(A1:A10)" in sheet_help, "Spreadsheets Help must include a range formula example"

    print("App Help contract: PASS")


if __name__ == "__main__":
    main()
