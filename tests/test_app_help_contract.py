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
    "txt": "Plain Text",
}


def main() -> None:
    for app, title in APPS.items():
        app_root = ROOT / "apps" / app
        help_file = app_root / "help" / "help.js"
        assert help_file.is_file(), f"{app}: app-local help/help.js is required"

        help_source = help_file.read_text(encoding="utf-8")
        assert "data-inkdos-help-entry" in help_source, f"{app}: Help menu entry marker missing"
        assert 'data-icon="CircleHelp"' in help_source, f"{app}: CircleHelp icon marker missing"
        assert ">Help</span>" in help_source, f"{app}: Help label missing"
        assert "data-inkdos-help-dialog" in help_source, f"{app}: Help dialog marker missing"
        assert title in help_source, f"{app}: Help content must be app-specific"

        # App Help stays inside its own app and is loaded explicitly by that app.
        if app == "txt":
            template = (app_root / "page.template.html").read_text(encoding="utf-8")
            assert "<!-- SCRIPT apps/txt/help/help.js -->" in template, "txt: Help must be part of the deterministic local bundle"
        else:
            index = (app_root / "index.html").read_text(encoding="utf-8")
            assert 'src="help/help.js"' in index, f"{app}: index must load its own Help module"

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
