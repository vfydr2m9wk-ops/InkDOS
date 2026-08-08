#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from browser_support import launch_browser
from zipfile import ZipFile
import json

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "compatibility-fixtures" / "spreadsheets" / "era2_office_2007_2013_baseline.xlsx"
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)


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
        "apps/spreadsheets/xlsx-engine.js",
        ROOT / "shared/office-shell.js",
        ROOT / "apps/spreadsheets/formula-safety.js",
        ROOT / "apps/spreadsheets/history-controller.js",
        ROOT / "apps/spreadsheets/worksheet-tabs.js",
        "apps/spreadsheets/app.js",
    ):
        page.add_script_tag(path=str(js))


def wait_open(page):
    page.wait_for_function("!document.querySelector('#gridViewport').hidden", timeout=30000)


def sheet_count(path: Path) -> int:
    with ZipFile(path) as z:
        workbook = z.read("xl/workbook.xml").decode("utf-8", "replace")
        return workbook.count("<sheet ")


def main() -> int:
    before = sheet_count(FIX)
    saved = OUT / "spreadsheet_add_sheet_02031.xlsx"
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 1400, "height": 900}, accept_downloads=True)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        load_app(page)
        page.set_input_files("#fileInput", str(FIX))
        wait_open(page)
        page.wait_for_selector("#addSheetBtn")
        page.locator("#addSheetBtn").evaluate("el => el.click()")
        active_name = page.locator("#sheetTabs button.active").inner_text()
        if not active_name.startswith("Sheet"):
            raise RuntimeError(f"Unexpected new sheet name: {active_name!r}")
        page.click('.cell[data-r="0"][data-c="0"]')
        page.fill("#formulaInput", "INKDESK-SECOND-SHEET")
        page.press("#formulaInput", "Enter")
        page.click("#saveBtn", force=True)
        page.wait_for_function("document.querySelector('#savePanel').style.display==='flex'", timeout=30000)
        with page.expect_download(timeout=30000) as info:
            page.click("#downloadBtn", force=True)
        info.value.save_as(str(saved))
        page.close()

        after = sheet_count(saved)
        if after != before + 1:
            raise RuntimeError(f"Expected one new worksheet: before={before}, after={after}")

        reopened = browser.new_page(viewport={"width": 1400, "height": 900})
        reopen_errors = []
        reopened.on("pageerror", lambda error: reopen_errors.append(str(error)))
        load_app(reopened)
        reopened.set_input_files("#fileInput", str(saved))
        wait_open(reopened)
        labels = reopened.locator("#sheetTabs button:not(#addSheetBtn)").all_inner_texts()
        if active_name not in labels:
            raise RuntimeError(f"New worksheet was not present after reopen: {labels!r}")
        reopened.locator("#sheetTabs button", has_text=active_name).evaluate("el => el.click()")
        marker = reopened.locator('.cell[data-r="0"][data-c="0"]').inner_text()
        reopened.close()
        browser.close()

    if marker != "INKDESK-SECOND-SHEET":
        raise RuntimeError(f"New worksheet content did not survive round-trip: {marker!r}")
    if errors or reopen_errors:
        raise RuntimeError(f"Browser errors: initial={errors}, reopen={reopen_errors}")
    result = {"before": before, "after": after, "sheet": active_name, "marker": marker}
    (OUT / "spreadsheet_add_sheet_02031.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
