"""Verify export lifecycle behavior through each real workspace UI."""
from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

from browser_support import launch_browser

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
FIXTURES = {
    "documents": ROOT / "tests/compatibility-fixtures/documents/era2_office_2007_2013_baseline.docx",
    "spreadsheets": ROOT / "tests/compatibility-fixtures/spreadsheets/era2_office_2007_2013_baseline.xlsx",
    "presentations": ROOT / "tests/compatibility-fixtures/presentations/era2_office_2007_2013_baseline.pptx",
}
SCRIPTS = {
    "documents": (
        "shared/vendor/pako_inflate.min.js", "shared/office-runtime.js", "shared/file-lifecycle.js",
        "shared/safe-dom.js", "apps/documents/docx-parser.js", "shared/vendor/jszip.min.js",
        "apps/documents/docx-writer.js", "shared/office-shell.js", "apps/documents/app.js",
    ),
    "spreadsheets": (
        "shared/office-runtime.js", "shared/file-lifecycle.js", "shared/formula-engine.js",
        "shared/vendor/jszip.min.js", "apps/spreadsheets/xls-biff8-engine.js",
        "apps/spreadsheets/xlsx-engine.js", "shared/office-shell.js", "apps/spreadsheets/app.js",
    ),
    "presentations": (
        "shared/office-runtime.js", "shared/file-lifecycle.js", "shared/vendor/jszip.min.js",
        "apps/presentations/engine/compatibility.js", "shared/office-shell.js", "apps/presentations/app.js",
    ),
}


def load_app(page: Page, workspace: str) -> None:
    soup = BeautifulSoup((ROOT / f"apps/{workspace}/index.html").read_text(encoding="utf-8"), "html.parser")
    for node in soup.find_all(["script", "link"]):
        node.decompose()
    page.set_content(str(soup), wait_until="domcontentloaded")
    page.add_style_tag(path=str(ROOT / f"apps/{workspace}/styles.css"))
    page.add_style_tag(path=str(ROOT / "shared/office-shell.css"))
    for script in SCRIPTS[workspace]:
        page.add_script_tag(path=str(ROOT / script))


def beforeunload_warns(page: Page) -> bool:
    return page.evaluate("""() => {
      const event=new Event('beforeunload',{cancelable:true});
      window.dispatchEvent(event);
      return event.defaultPrevented;
    }""")


def block_download(page: Page) -> None:
    page.evaluate("""() => {
      window.__realInkDeskRuntime=window.InkDeskRuntime;
      window.InkDeskRuntime=Object.freeze(Object.assign({},window.InkDeskRuntime,{
        requestDownload(){throw new Error('blocked by lifecycle regression')}
      }));
    }""")


def restore_download(page: Page) -> None:
    page.evaluate("window.InkDeskRuntime=window.__realInkDeskRuntime")


def verify_documents(context) -> dict:
    page = context.new_page()
    dialogs=[]
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
    load_app(page, "documents")
    page.set_input_files("#fileInput", str(FIXTURES["documents"]))
    page.wait_for_function("document.querySelector('#pagesHost').innerText.includes('ERA2-DOCX-MARKER')")
    page.evaluate("""() => {const p=document.createElement('p');p.textContent='LIFECYCLE-DOCX';const host=document.querySelector('.page-content');host.appendChild(p);host.dispatchEvent(new InputEvent('input',{bubbles:true,data:'x'}));}""")
    page.wait_for_timeout(350)
    if not beforeunload_warns(page): raise RuntimeError("DOCX edit did not enable beforeunload")
    block_download(page)
    page.click("#saveBtn"); page.wait_for_selector("#saveReadyPanel"); page.click("#saveCopyDownload")
    if "Export failed" not in page.locator("#statusText").inner_text(): raise RuntimeError("DOCX blocked download did not fail")
    if not beforeunload_warns(page): raise RuntimeError("DOCX export failure cleared warning")
    restore_download(page)
    output=OUT/"lifecycle_document.docx"
    with page.expect_download(timeout=30000) as info: page.click("#saveCopyDownload")
    info.value.save_as(str(output))
    if "not verified" not in page.locator("#statusText").inner_text().lower(): raise RuntimeError("DOCX download claimed verification")
    if not beforeunload_warns(page): raise RuntimeError("DOCX unverified download cleared warning")
    page.set_input_files("#fileInput", str(output))
    page.wait_for_function("document.querySelector('#statusText').textContent.includes('reopened successfully')")
    if beforeunload_warns(page): raise RuntimeError("DOCX verified reopen retained warning")
    result={"workspace":"documents","dialogs":dialogs,"verified":True}
    page.close(); return result


def verify_spreadsheets(context) -> dict:
    page = context.new_page()
    dialogs=[]
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
    load_app(page, "spreadsheets")
    page.set_input_files("#fileInput", str(FIXTURES["spreadsheets"]))
    page.wait_for_function("!document.querySelector('#gridViewport').hidden && !document.querySelector('#loading').offsetParent")
    page.click('.cell[data-r="15"][data-c="0"]'); page.fill("#formulaInput", "LIFECYCLE-XLSX"); page.press("#formulaInput", "Enter")
    if not beforeunload_warns(page): raise RuntimeError("XLSX edit did not enable beforeunload")
    page.click("#saveBtn"); page.wait_for_function("document.querySelector('#savePanel').style.display==='flex'")
    block_download(page); page.click("#downloadBtn")
    if "Export failed" not in page.locator("#saveMessage").inner_text(): raise RuntimeError("XLSX blocked download did not fail")
    if not beforeunload_warns(page): raise RuntimeError("XLSX export failure cleared warning")
    restore_download(page)
    output=OUT/"lifecycle_spreadsheet.xlsx"
    with page.expect_download(timeout=30000) as info: page.click("#downloadBtn")
    info.value.save_as(str(output))
    if "not verified" not in page.locator("#saveMessage").inner_text().lower(): raise RuntimeError("XLSX download claimed verification")
    if not beforeunload_warns(page): raise RuntimeError("XLSX unverified download cleared warning")
    page.set_input_files("#fileInput", str(output))
    page.wait_for_function("document.querySelector('#saveMessage').textContent.includes('reopened successfully')")
    if beforeunload_warns(page): raise RuntimeError("XLSX verified reopen retained warning")
    result={"workspace":"spreadsheets","dialogs":dialogs,"verified":True}
    page.close(); return result


def verify_presentations(context) -> dict:
    page = context.new_page()
    dialogs=[]
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
    load_app(page, "presentations")
    page.set_input_files("#fileInput", str(FIXTURES["presentations"]))
    page.wait_for_function("window.__LocalPresentationsDebug && window.__LocalPresentationsDebug.slideCount > 0")
    object_id=page.evaluate("window.__LocalPresentationsDebug.getPresentation().slides[0].objects.find(o=>o.type==='text'&&o.sourceLayer==='slide'&&!o.templateObject).id")
    page.evaluate("""id => document.querySelector('#slideCanvas [data-id="'+id+'"]').dispatchEvent(new MouseEvent('dblclick',{bubbles:true}))""", object_id)
    editor=page.locator(f'#slideCanvas [data-id="{object_id}"] .editable[contenteditable="true"]')
    editor.fill(editor.inner_text()+"\nLIFECYCLE-PPTX"); editor.blur()
    if not beforeunload_warns(page): raise RuntimeError("PPTX edit did not enable beforeunload")
    block_download(page); page.click("#saveBtn")
    page.wait_for_function("document.querySelector('#stateBadge').textContent==='Export failed'")
    if not beforeunload_warns(page): raise RuntimeError("PPTX export failure cleared warning")
    restore_download(page)
    output=OUT/"lifecycle_presentation.pptx"
    with page.expect_download(timeout=30000) as info: page.click("#saveBtn")
    info.value.save_as(str(output))
    if "not verified" not in page.locator("#stateBadge").inner_text().lower(): raise RuntimeError("PPTX download claimed verification")
    if not beforeunload_warns(page): raise RuntimeError("PPTX unverified download cleared warning")
    page.set_input_files("#fileInput", str(output))
    page.wait_for_function("document.querySelector('#stateBadge').textContent.includes('reopened successfully')")
    if beforeunload_warns(page): raise RuntimeError("PPTX verified reopen retained warning")
    result={"workspace":"presentations","dialogs":dialogs,"verified":True}
    page.close(); return result


def main() -> None:
    with sync_playwright() as playwright:
        browser=launch_browser(playwright)
        context=browser.new_context(viewport={"width":1400,"height":900},accept_downloads=True)
        results=[verify_documents(context),verify_spreadsheets(context),verify_presentations(context)]
        context.close();browser.close()
    (OUT/"export_lifecycle_workspaces.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(json.dumps(results,indent=2))


if __name__ == "__main__":
    main()
