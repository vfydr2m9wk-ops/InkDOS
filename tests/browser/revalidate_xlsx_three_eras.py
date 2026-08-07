"""Optional browser validation for XLS/BIFF8 import and XLSX round trips.

Requirements:
    pip install playwright beautifulsoup4
    A Chromium executable available as CHROMIUM_PATH or /usr/bin/chromium.

Run from the repository root:
    python3 tests/browser/revalidate_xlsx_three_eras.py
"""
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from browser_support import launch_browser, requested_browser_name
from zipfile import ZipFile
import json
import os
import re

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "compatibility-fixtures" / "spreadsheets"
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")


def load_app(page):
    soup = BeautifulSoup((ROOT / "apps/spreadsheets/index.html").read_text(), "html.parser")
    for node in soup.find_all(["script", "link"]):
        node.decompose()
    base = soup.new_tag("base", href=ROOT.as_uri() + "/")
    if soup.head:
        soup.head.insert(0, base)
    page.set_content(str(soup), wait_until="domcontentloaded")
    for css in (ROOT / "apps/spreadsheets/styles.css", ROOT / "shared/office-shell.css"):
        page.add_style_tag(path=str(css))
    for js in (
        ROOT / "shared/office-runtime.js",
                ROOT / "shared/vendor/jszip.min.js",
        ROOT / "apps/spreadsheets/xls-biff8-engine.js",
        ROOT / "apps/spreadsheets/xlsx-engine.js",
        ROOT / "shared/office-shell.js",
        ROOT / "apps/spreadsheets/app.js",
    ):
        page.add_script_tag(path=str(js))


def wait_open(page):
    page.wait_for_function(
        "!document.querySelector('#gridViewport').hidden && !document.querySelector('#loading').offsetParent",
        timeout=30000,
    )


def package_features(path):
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        sheets = [archive.read(n).decode("utf-8", "replace") for n in names if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
        joined = "\n".join(sheets)
        workbook = archive.read("xl/workbook.xml").decode("utf-8", "replace")
        return {
            "parts": len(names),
            "drawing": "<drawing" in joined,
            "pane": "<pane" in joined,
            "columns": "<cols" in joined,
            "page_setup": "<pageSetup" in joined,
            "filter": "<autoFilter" in joined,
            "table_parts": "<tableParts" in joined,
            "conditional_formatting": "<conditionalFormatting" in joined,
            "data_validation": "<dataValidation" in joined,
            "chart_parts": any(n.startswith("xl/charts/") for n in names),
            "media_parts": len([n for n in names if n.startswith("xl/media/")]),
            "hidden_sheet": 'state="hidden"' in workbook,
            "modern_formulas": all(token in joined for token in ("XLOOKUP", "FILTER", "LET")),
        }


def edit_and_download(page, row, output):
    marker = "XLSX-ROUNDTRIP-REGRESSION-MARKER"
    page.click(f'.cell[data-r="{row}"][data-c="0"]')
    page.fill("#formulaInput", marker)
    page.press("#formulaInput", "Enter")
    page.click("#saveBtn")
    page.wait_for_function("document.querySelector('#savePanel').style.display==='flex'", timeout=30000)
    with page.expect_download(timeout=30000) as download_info:
        page.click("#downloadBtn")
    download_info.value.save_as(str(output))
    return marker


def main():
    results = []
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        for filename in (
            "era1_office_97_2003_legacy.xls",
            "era2_office_2007_2013_baseline.xlsx",
            "era3_office_2016_365_modern.xlsx",
        ):
            page = browser.new_page(viewport={"width": 1500, "height": 1100}, accept_downloads=True)
            dialogs, errors = [], []
            page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
            page.on("pageerror", lambda error: errors.append(str(error)))
            load_app(page)
            page.set_input_files("#fileInput", str(FIX / filename))
            wait_open(page)

            is_legacy = filename.endswith(".xls")
            original = None if is_legacy else package_features(FIX / filename)
            saved = OUT / (filename + ".saved.xlsx")
            marker_row = 12 if is_legacy else 9
            marker = edit_and_download(page, marker_row, saved)
            exported = package_features(saved)
            opened = {
                "tabs": page.locator("#sheetTabs button").all_inner_texts(),
                "images": page.locator(".sheet-image").count(),
                "charts": page.locator(".sheet-chart").count(),
                "errors": errors,
                "dialogs": dialogs,
            }
            page.close()

            reopened = browser.new_page(viewport={"width": 1500, "height": 1100})
            reopen_errors = []
            reopened.on("pageerror", lambda error: reopen_errors.append(str(error)))
            load_app(reopened)
            reopened.set_input_files("#fileInput", str(saved))
            wait_open(reopened)
            marker_text = reopened.locator(f'.cell[data-r="{marker_row}"][data-c="0"]').inner_text()
            reopen_data = {
                "marker": marker_text,
                "images": reopened.locator(".sheet-image").count(),
                "errors": reopen_errors,
            }
            reopened.close()

            if marker_text != marker:
                raise RuntimeError(f"Edited marker was not retained for {filename}: {marker_text!r}")
            if errors or reopen_errors or dialogs:
                raise RuntimeError(f"Browser errors for {filename}: dialogs={dialogs}, errors={errors}, reopen={reopen_errors}")
            if is_legacy and opened["images"] and exported["media_parts"] < 1:
                raise RuntimeError("Legacy XLS image was not exported to XLSX")

            results.append({
                "file": filename,
                "legacy_import": is_legacy,
                "opened": opened,
                "original": original,
                "exported": exported,
                "reopened": reopen_data,
            })
        browser.close()
    (OUT / "xlsx_three_eras.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
