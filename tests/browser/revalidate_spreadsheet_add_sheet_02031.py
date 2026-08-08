#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from browser_support import launch_browser
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import json

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "compatibility-fixtures" / "spreadsheets" / "era2_office_2007_2013_baseline.xlsx"
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def load_app(page):
    soup = BeautifulSoup((ROOT / "apps/spreadsheets/index.html").read_text(), "html.parser")
    for node in soup.find_all(["script", "link"]):
        node.decompose()
    base = soup.new_tag("base", href=ROOT.as_uri() + "/")
    soup.head.insert(0, base)
    page.set_content(str(soup), wait_until="domcontentloaded")
    for css in (
        ROOT / "apps/spreadsheets/styles.css",
        ROOT / "shared/office-shell.css",
        ROOT / "shared/ui/design-tokens.css",
        ROOT / "shared/ui/components.css",
        ROOT / "shared/ui/workspace-layout.css",
        ROOT / "shared/ui/visual-foundation.css",
        ROOT / "shared/ui/visual-foundation-v0203.css",
        ROOT / "shared/ui/content-workspaces-v02031.css",
        ROOT / "shared/ui/workspace-unification-v02031.css",
    ):
        page.add_style_tag(path=str(css))
    for js in (
        ROOT / "shared/office-runtime.js",
        ROOT / "shared/vendor/jszip.min.js",
        ROOT / "apps/spreadsheets/xls-biff8-engine.js",
        ROOT / "apps/spreadsheets/worksheet-package.js",
        ROOT / "apps/spreadsheets/xlsx-engine.js",
        ROOT / "shared/office-shell.js",
        ROOT / "apps/spreadsheets/formula-safety.js",
        ROOT / "apps/spreadsheets/history-controller.js",
        ROOT / "apps/spreadsheets/worksheet-tabs.js",
        ROOT / "apps/spreadsheets/app.js",
    ):
        page.add_script_tag(path=str(js))


def wait_open(page):
    page.wait_for_function("!document.querySelector('#gridViewport').hidden", timeout=30000)


def sheet_names(path: Path) -> list[str]:
    with ZipFile(path) as z:
        root = ET.fromstring(z.read("xl/workbook.xml"))
        return [node.attrib.get("name", "") for node in root.findall(".//x:sheet", NS)]


def save_workbook(page, path: Path):
    page.click("#saveBtn", force=True)
    page.wait_for_function("document.querySelector('#savePanel').style.display==='flex'", timeout=30000)
    with page.expect_download(timeout=30000) as info:
        page.click("#downloadBtn", force=True)
    info.value.save_as(str(path))


def delete_active(page, accept: bool):
    dialogs = []
    def handle(dialog):
        dialogs.append(dialog.message)
        dialog.accept() if accept else dialog.dismiss()
    page.once("dialog", handle)
    page.locator("#deleteSheetBtn").evaluate("el => el.click()")
    page.wait_for_timeout(120)
    if not dialogs:
        raise RuntimeError("Delete worksheet did not request confirmation")


def main() -> int:
    before_names = sheet_names(FIX)
    if len(before_names) < 2:
        raise RuntimeError(f"Fixture must contain at least two worksheets: {before_names!r}")
    added = OUT / "spreadsheet_add_sheet_02031.xlsx"
    deleted = OUT / "spreadsheet_delete_sheet_02031.xlsx"

    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 1400, "height": 900}, accept_downloads=True)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        load_app(page)
        page.set_input_files("#fileInput", str(FIX))
        wait_open(page)
        page.wait_for_selector("#addSheetBtn")
        if page.locator("#deleteSheetBtn").is_disabled():
            raise RuntimeError("Delete worksheet should be enabled for a multi-sheet workbook")

        page.locator("#addSheetBtn").evaluate("el => el.click()")
        active_name = page.locator("#sheetTabs button.active").inner_text()
        if not active_name.startswith("Sheet"):
            raise RuntimeError(f"Unexpected new sheet name: {active_name!r}")
        page.click('.cell[data-r="0"][data-c="0"]')
        page.fill("#formulaInput", "INKDESK-SECOND-SHEET")
        page.press("#formulaInput", "Enter")
        save_workbook(page, added)
        page.close()

        added_names = sheet_names(added)
        if len(added_names) != len(before_names) + 1 or active_name not in added_names:
            raise RuntimeError(f"Add worksheet round-trip failed: before={before_names!r}, after={added_names!r}")

        reopened = browser.new_page(viewport={"width": 1400, "height": 900}, accept_downloads=True)
        reopen_errors = []
        reopened.on("pageerror", lambda error: reopen_errors.append(str(error)))
        load_app(reopened)
        reopened.set_input_files("#fileInput", str(added))
        wait_open(reopened)
        labels = reopened.locator("#sheetTabs button:not(#addSheetBtn):not(#deleteSheetBtn)").all_inner_texts()
        if active_name not in labels:
            raise RuntimeError(f"New worksheet was not present after reopen: {labels!r}")
        reopened.locator("#sheetTabs button", has_text=active_name).evaluate("el => el.click()")
        marker = reopened.locator('.cell[data-r="0"][data-c="0"]').inner_text()
        if marker != "INKDESK-SECOND-SHEET":
            raise RuntimeError(f"New worksheet content did not survive round-trip: {marker!r}")

        victim = before_names[0]
        reopened.locator("#sheetTabs button", has_text=victim).evaluate("el => el.click()")
        count_before_cancel = reopened.locator("#sheetTabs button:not(#addSheetBtn):not(#deleteSheetBtn)").count()
        delete_active(reopened, accept=False)
        count_after_cancel = reopened.locator("#sheetTabs button:not(#addSheetBtn):not(#deleteSheetBtn)").count()
        if count_after_cancel != count_before_cancel:
            raise RuntimeError("Cancelling worksheet deletion changed the workbook")

        delete_active(reopened, accept=True)
        labels_after_delete = reopened.locator("#sheetTabs button:not(#addSheetBtn):not(#deleteSheetBtn)").all_inner_texts()
        if victim in labels_after_delete:
            raise RuntimeError(f"Deleted worksheet remains visible: {labels_after_delete!r}")
        save_workbook(reopened, deleted)
        reopened.close()

        deleted_names = sheet_names(deleted)
        if victim in deleted_names or active_name not in deleted_names or len(deleted_names) != len(before_names):
            raise RuntimeError(f"Delete worksheet round-trip failed: {deleted_names!r}")

        final_page = browser.new_page(viewport={"width": 1400, "height": 900})
        final_errors = []
        final_page.on("pageerror", lambda error: final_errors.append(str(error)))
        load_app(final_page)
        final_page.set_input_files("#fileInput", str(deleted))
        wait_open(final_page)
        final_labels = final_page.locator("#sheetTabs button:not(#addSheetBtn):not(#deleteSheetBtn)").all_inner_texts()
        if final_labels != deleted_names:
            raise RuntimeError(f"Reopened worksheet labels differ from package registry: {final_labels!r} vs {deleted_names!r}")
        final_page.locator("#sheetTabs button", has_text=active_name).evaluate("el => el.click()")
        final_marker = final_page.locator('.cell[data-r="0"][data-c="0"]').inner_text()
        if final_marker != "INKDESK-SECOND-SHEET":
            raise RuntimeError(f"Surviving worksheet content was damaged by deletion: {final_marker!r}")
        # Delete the added sheet in-memory; the final visible sheet must become protected from deletion.
        delete_active(final_page, accept=True)
        if not final_page.locator("#deleteSheetBtn").is_disabled():
            raise RuntimeError("Delete worksheet must be disabled when only one visible worksheet remains")
        final_page.close()
        browser.close()

    if errors or reopen_errors or final_errors:
        raise RuntimeError(f"Browser errors: initial={errors}, reopen={reopen_errors}, final={final_errors}")
    result = {
        "before": before_names,
        "after_add": added_names,
        "after_delete": deleted_names,
        "deleted": victim,
        "survivor": active_name,
        "marker": final_marker,
        "last_sheet_delete_disabled": True,
    }
    (OUT / "spreadsheet_add_sheet_02031.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
