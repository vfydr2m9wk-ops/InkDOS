"""Open and edit all workspaces in one browser session without state crossover."""
from __future__ import annotations

import json
import os
from pathlib import Path
from zipfile import ZipFile

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")
DOCX = ROOT / "tests/compatibility-fixtures/documents/era2_office_2007_2013_baseline.docx"
XLSX = ROOT / "tests/compatibility-fixtures/spreadsheets/era2_office_2007_2013_baseline.xlsx"
PPTX = ROOT / "tests/compatibility-fixtures/presentations/era2_office_2007_2013_baseline.pptx"
MARKERS = {
    "documents": "CROSS-DOCUMENT-MARKER",
    "spreadsheets": "CROSS-SPREADSHEET-MARKER",
    "presentations": "CROSS-PRESENTATION-MARKER",
}

SCRIPTS = {
    "documents": (
        "shared/vendor/pako_inflate.min.js",
        "shared/office-runtime.js",
        "apps/documents/drawing-layout.js",
        "apps/documents/docx-parser.js",
        "shared/vendor/jszip.min.js",
        "apps/documents/docx-writer.js",
        "shared/office-shell.js",
        "apps/documents/app.js",
    ),
    "spreadsheets": (
        "shared/office-runtime.js",
        "shared/vendor/jszip.min.js",
        "apps/spreadsheets/xls-biff8-engine.js",
        "apps/spreadsheets/worksheet-package.js",
        "apps/spreadsheets/xlsx-engine.js",
        "shared/office-shell.js",
        "apps/spreadsheets/formula-safety.js",
        "apps/spreadsheets/history-controller.js",
        "apps/spreadsheets/worksheet-tabs.js",
        "apps/spreadsheets/app.js",
    ),
    "presentations": (
        "shared/office-runtime.js",
        "shared/vendor/jszip.min.js",
        "apps/presentations/engine/compatibility.js",
        "apps/presentations/engine/background-resolver.js",
        "shared/office-shell.js",
        "apps/presentations/state/selection-controller.js",
        "apps/presentations/state/history-controller.js",
        "apps/presentations/ui/inspector-controller.js",
        "apps/presentations/ui/thumbnails-controller.js",
        "apps/presentations/ui/presenter-notes-controller.js",
        "apps/presentations/presentation/slideshow-controller.js",
        "apps/presentations/io/pptx-write-adapter.js",
        "apps/presentations/io/file-controller.js",
        "apps/presentations/io/recovery-controller.js",
        "apps/presentations/app.js",
    ),
}


def load_app(page, workspace):
    soup = BeautifulSoup((ROOT / f"apps/{workspace}/index.html").read_text(encoding="utf-8"), "html.parser")
    for node in soup.find_all(["script", "link"]):
        node.decompose()
    base = soup.new_tag("base", href=ROOT.as_uri() + "/")
    if soup.head:
        soup.head.insert(0, base)
    page.set_content(str(soup), wait_until="domcontentloaded")
    page.add_style_tag(path=str(ROOT / f"apps/{workspace}/styles.css"))
    page.add_style_tag(path=str(ROOT / "shared/office-shell.css"))
    for script in SCRIPTS[workspace]:
        page.add_script_tag(path=str(ROOT / script))


def edit_document(page):
    marker = MARKERS["documents"]
    page.evaluate(
        """marker => {
          const host=document.querySelector('.page-content');
          const paragraph=document.createElement('p');
          paragraph.textContent=marker;
          host.appendChild(paragraph);
          host.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:marker}));
        }""",
        marker,
    )
    page.wait_for_timeout(500)
    page.click("#undoBtn")
    if marker in page.locator("#pagesHost").inner_text():
        raise RuntimeError("Document undo did not isolate the latest edit")
    page.click("#redoBtn")
    if marker not in page.locator("#pagesHost").inner_text():
        raise RuntimeError("Document redo did not restore the latest edit")
    page.fill("#titleText", "Cross Workspace Document.docx")
    page.locator("#titleText").blur()


def edit_spreadsheet(page):
    marker = MARKERS["spreadsheets"]
    page.click('.cell[data-r="15"][data-c="0"]')
    page.fill("#formulaInput", marker)
    page.press("#formulaInput", "Enter")
    page.click("#undoBtn")
    if page.locator('.cell[data-r="15"][data-c="0"]').inner_text() == marker:
        raise RuntimeError("Spreadsheet undo did not isolate the latest edit")
    page.click("#redoBtn")
    if page.locator('.cell[data-r="15"][data-c="0"]').inner_text() != marker:
        raise RuntimeError("Spreadsheet redo did not restore the latest edit")


def edit_presentation(page):
    marker = MARKERS["presentations"]
    object_id = page.evaluate(
        """() => window.__LocalPresentationsDebug.getPresentation().slides[0].objects.find(
          object => object.type==='text' && object.sourceLayer==='slide' && !object.templateObject
        ).id"""
    )
    page.evaluate(
        '''id => document.querySelector('#slideCanvas [data-id="'+id+'"]').dispatchEvent(new MouseEvent('dblclick',{bubbles:true}))''',
        object_id,
    )
    editor = page.locator(f'#slideCanvas [data-id="{object_id}"] .editable[contenteditable="true"]')
    editor.fill(editor.inner_text() + "\n" + marker)
    editor.blur()
    page.click("#undoBtn")
    state = page.evaluate("window.__LocalPresentationsDebug.getPresentation().slides[0].objects.map(o=>o.text||'').join('|')")
    if marker in state:
        raise RuntimeError("Presentation undo did not isolate the latest edit")
    page.click("#redoBtn")
    state = page.evaluate("window.__LocalPresentationsDebug.getPresentation().slides[0].objects.map(o=>o.text||'').join('|')")
    if marker not in state:
        raise RuntimeError("Presentation redo did not restore the latest edit")


def save_document(page, destination):
    page.click("#saveBtn")
    page.wait_for_selector("#saveReadyPanel")
    with page.expect_download(timeout=30000) as info:
        page.click("#saveCopyDownload")
    info.value.save_as(str(destination))


def save_spreadsheet(page, destination):
    page.click("#saveBtn")
    page.wait_for_function("document.querySelector('#savePanel').style.display==='flex'", timeout=30000)
    with page.expect_download(timeout=30000) as info:
        page.click("#downloadBtn")
    info.value.save_as(str(destination))


def save_presentation(page, destination):
    with page.expect_download(timeout=30000) as info:
        page.click("#saveBtn")
    info.value.save_as(str(destination))


def package_contains(path: Path, marker: str, prefix: str) -> bool:
    with ZipFile(path) as package:
        return any(marker.encode() in package.read(name) for name in package.namelist() if name.startswith(prefix) and name.endswith(".xml"))


def main():
    outputs = {
        "documents": OUT / "cross_workspace_document.docx",
        "spreadsheets": OUT / "cross_workspace_spreadsheet.xlsx",
        "presentations": OUT / "cross_workspace_presentation.pptx",
    }
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        context = browser.new_context(viewport={"width": 1400, "height": 900}, accept_downloads=True)
        pages = {}
        errors = {}
        for workspace in SCRIPTS:
            page = context.new_page()
            errors[workspace] = []
            page.on("pageerror", lambda error, workspace=workspace: errors[workspace].append(str(error)))
            page.on("dialog", lambda dialog: dialog.accept())
            load_app(page, workspace)
            pages[workspace] = page

        pages["documents"].set_input_files("#fileInput", str(DOCX))
        pages["documents"].wait_for_function("document.querySelector('#pagesHost').innerText.includes('ERA2-DOCX-MARKER')")
        pages["spreadsheets"].set_input_files("#fileInput", str(XLSX))
        pages["spreadsheets"].wait_for_function("!document.querySelector('#gridViewport').hidden && !document.querySelector('#loading').offsetParent")
        pages["presentations"].set_input_files("#fileInput", str(PPTX))
        pages["presentations"].wait_for_function("window.__LocalPresentationsDebug && window.__LocalPresentationsDebug.slideCount > 0")

        edit_document(pages["documents"])
        edit_spreadsheet(pages["spreadsheets"])
        edit_presentation(pages["presentations"])

        for _ in range(5):
            for workspace in ("documents", "spreadsheets", "presentations"):
                pages[workspace].bring_to_front()
                pages[workspace].wait_for_timeout(40)

        bodies = {workspace: page.locator("body").inner_text() for workspace, page in pages.items()}
        for workspace, marker in MARKERS.items():
            if marker not in bodies[workspace]:
                raise RuntimeError(f"Own marker disappeared from {workspace}")
            for other_workspace, other_body in bodies.items():
                if other_workspace != workspace and marker in other_body:
                    raise RuntimeError(f"Marker from {workspace} contaminated {other_workspace}")

        if pages["documents"].locator("#titleText").input_value() != "Cross Workspace Document.docx":
            raise RuntimeError("Document rename did not remain isolated")
        if pages["spreadsheets"].locator("#docTitle").input_value() != XLSX.name:
            raise RuntimeError("Spreadsheet filename changed during another workspace rename")
        if pages["presentations"].locator("#docTitle").input_value() != PPTX.name:
            raise RuntimeError("Presentation filename changed during another workspace rename")

        save_document(pages["documents"], outputs["documents"])
        save_spreadsheet(pages["spreadsheets"], outputs["spreadsheets"])
        save_presentation(pages["presentations"], outputs["presentations"])
        context.close()
        browser.close()

    package_checks = {
        "documents": package_contains(outputs["documents"], MARKERS["documents"], "word/"),
        "spreadsheets": package_contains(outputs["spreadsheets"], MARKERS["spreadsheets"], "xl/worksheets/"),
        "presentations": package_contains(outputs["presentations"], MARKERS["presentations"], "ppt/slides/"),
    }
    if not all(package_checks.values()):
        raise RuntimeError(f"A workspace saved stale or foreign content: {package_checks}")
    if any(errors.values()):
        raise RuntimeError(f"Unexpected page errors: {errors}")

    result = {"switch_rounds": 5, "markers": MARKERS, "package_checks": package_checks, "page_errors": errors}
    (OUT / "cross_workspace_isolation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
