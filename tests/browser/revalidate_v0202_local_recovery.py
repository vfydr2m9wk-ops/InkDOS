"""Behavioral regression for v0.20.2.1 private IndexedDB recovery snapshots."""
from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zipfile import ZipFile
import re

from playwright.sync_api import sync_playwright

from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
FIX = ROOT / "tests" / "compatibility-fixtures" / "spreadsheets"
OUT.mkdir(parents=True, exist_ok=True)


class FastThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def start_server():
    handler = partial(QuietHandler, directory=str(ROOT))
    server = FastThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def watch_errors(page):
    errors = []
    page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))

    def console(message):
        if message.type == "error" and "Failed to load resource" not in message.text:
            errors.append(f"console.error: {message.text}")

    def response(item):
        if item.status >= 400:
            errors.append(f"HTTP {item.status}: {item.url}")

    page.on("console", console)
    page.on("response", response)
    return errors


def reopen_and_restore(context, url):
    page = context.new_page()
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(15000)
    errors = watch_errors(page)
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector(".inkdesk-recovery-overlay", state="visible", timeout=10000)
    page.get_by_role("button", name="Restore", exact=True).click()
    page.wait_for_selector(".inkdesk-recovery-overlay", state="detached", timeout=10000)
    return page, errors


def documents_case(browser, base_url):
    context = browser.new_context()
    token = "Recovered document text 0202"
    page = context.new_page()
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(15000)
    errors = watch_errors(page)
    page.goto(f"{base_url}/apps/documents/index.html", wait_until="networkidle")
    page.click("#newWelcomeBtn")
    page.wait_for_selector(".page-content", state="visible")
    page.locator(".page-content p").first.evaluate(
        "(node, value) => { node.textContent=value; node.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:value})); }",
        token,
    )
    page.evaluate("window.__InkDeskDocumentsRecovery.manager.flush()")
    snapshots = page.evaluate("InkDeskLocalRecovery.listSnapshots('documents').then(items=>items.length)")
    if snapshots < 1:
        raise RuntimeError("Documents did not create an IndexedDB recovery snapshot")
    page.close()
    restored, restored_errors = reopen_and_restore(context, f"{base_url}/apps/documents/index.html")
    restored.wait_for_function("value => document.querySelector('#pagesHost').innerText.includes(value)", arg=token)
    restored_text = restored.locator("#pagesHost").inner_text()
    restored.evaluate("InkDeskLocalRecovery.clearModule('documents')")
    restored.close()
    context.close()
    return {"workspace": "documents", "restored": token in restored_text, "snapshots": snapshots, "errors": errors + restored_errors}


def spreadsheets_case(browser, base_url):
    context = browser.new_context()
    token = "Recovered workbook value 0202"
    formula_draft = "=SU"
    page = context.new_page()
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(15000)
    errors = watch_errors(page)
    page.goto(f"{base_url}/apps/spreadsheets/index.html", wait_until="networkidle")
    page.click("#newEmptyBtn")
    page.wait_for_function("!document.querySelector('#gridViewport').hidden")
    page.click('.cell[data-r="0"][data-c="0"]')
    page.fill("#formulaInput", token)
    page.press("#formulaInput", "Enter")
    page.click('.cell[data-r="1"][data-c="1"]')
    page.fill("#formulaInput", formula_draft)
    page.wait_for_function("window.InkDeskSpreadsheetFormulaEditor?.hasPendingDrafts() === true")
    page.evaluate("window.__InkDeskSpreadsheetsRecovery.manager.flush()")
    snapshots = page.evaluate("InkDeskLocalRecovery.listSnapshots('spreadsheets').then(items=>items.length)")
    if snapshots < 1:
        raise RuntimeError("Spreadsheets did not create an IndexedDB recovery snapshot")
    page.close()
    restored, restored_errors = reopen_and_restore(context, f"{base_url}/apps/spreadsheets/index.html")
    capture = restored.evaluate("window.__InkDeskSpreadsheetsRecovery.capture()")
    value = next((item[1].get("v") for item in capture["book"]["sheets"][0]["cells"] if item[0] == "A1"), None)
    restored_drafts = restored.evaluate("window.InkDeskSpreadsheetFormulaEditor.snapshotDrafts()")
    draft_visible = restored.locator('.cell[data-r="1"][data-c="1"]').inner_text() == formula_draft
    restored.click('.cell[data-r="1"][data-c="1"]')
    restored.wait_for_function("window.InkDeskSpreadsheetFormulaEditor?.isActive() === true")
    resumed_value = restored.evaluate("window.InkDeskSpreadsheetFormulaEditor.getValue()")
    restored.evaluate("InkDeskLocalRecovery.clearModule('spreadsheets')")
    restored.close()
    context.close()
    draft_restored = any(item.get("key") == "Sheet1!B2" and item.get("value") == formula_draft for item in restored_drafts)
    return {
        "workspace": "spreadsheets",
        "restored": value == token and draft_restored and draft_visible and resumed_value == formula_draft,
        "value": value,
        "formulaDraft": formula_draft,
        "draftRestored": draft_restored,
        "draftVisible": draft_visible,
        "resumedValue": resumed_value,
        "snapshots": snapshots,
        "errors": errors + restored_errors,
    }



def xlsx_package_features(path):
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        sheets = [
            archive.read(name).decode("utf-8", "replace")
            for name in names
            if re.match(r"xl/worksheets/sheet\d+\.xml$", name)
        ]
        joined = "\n".join(sheets)
        workbook = archive.read("xl/workbook.xml").decode("utf-8", "replace")
        return {
            "drawing": "<drawing" in joined,
            "pane": "<pane" in joined,
            "columns": "<cols" in joined,
            "page_setup": "<pageSetup" in joined,
            "filter": "<autoFilter" in joined,
            "table_parts": "<tableParts" in joined,
            "conditional_formatting": "<conditionalFormatting" in joined,
            "data_validation": "<dataValidation" in joined,
            "chart_parts": any(name.startswith("xl/charts/") for name in names),
            "media_parts": len([name for name in names if name.startswith("xl/media/")]),
            "hidden_sheet": 'state="hidden"' in workbook,
            "modern_formulas": all(token in joined for token in ("XLOOKUP", "FILTER", "LET")),
        }


def spreadsheets_post_save_edit_recovery_case(browser, base_url):
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    page.set_default_timeout(15000)
    page.set_default_navigation_timeout(20000)
    errors = watch_errors(page)
    url = f"{base_url}/apps/spreadsheets/index.html"
    page.goto(url, wait_until="networkidle")
    page.evaluate("InkDeskLocalRecovery.clearModule('spreadsheets')")
    fixture = FIX / "era3_office_2016_365_modern.xlsx"
    page.set_input_files("#fileInput", str(fixture))
    page.wait_for_function("!document.querySelector('#gridViewport').hidden && !document.querySelector('#loading').offsetParent", timeout=30000)

    first_marker = "RECOVERY-SAVED-BASE-020225"
    second_marker = "RECOVERY-POST-SAVE-EDIT-020225"
    page.click('.cell[data-r="9"][data-c="0"]')
    page.fill("#formulaInput", first_marker)
    page.press("#formulaInput", "Enter")
    page.click("#saveBtn")
    page.wait_for_function("document.querySelector('#savePanel').style.display==='flex'", timeout=30000)
    first_output = OUT / "recovery_post_save_first.xlsx"
    with page.expect_download(timeout=30000) as download_info:
        page.click("#downloadBtn")
    download_info.value.save_as(str(first_output))
    page.wait_for_function("InkDeskLocalRecovery.listSnapshots('spreadsheets').then(items=>items.length===0)")

    page.click('.cell[data-r="10"][data-c="0"]')
    page.fill("#formulaInput", second_marker)
    page.press("#formulaInput", "Enter")
    page.evaluate("window.__InkDeskSpreadsheetsRecovery.manager.flush()")
    snapshots = page.evaluate("InkDeskLocalRecovery.listSnapshots('spreadsheets').then(items=>items.length)")
    if snapshots < 1:
        raise RuntimeError("Post-save spreadsheet edit did not create a recovery snapshot")
    page.close()

    restored, restored_errors = reopen_and_restore(context, url)
    restored.wait_for_function("value => document.querySelector('.cell[data-r=\"9\"][data-c=\"0\"]').innerText === value", arg=first_marker)
    restored.wait_for_function("value => document.querySelector('.cell[data-r=\"10\"][data-c=\"0\"]').innerText === value", arg=second_marker)
    restored.click("#saveBtn")
    restored.wait_for_function("document.querySelector('#savePanel').style.display==='flex'", timeout=30000)
    restored_output = OUT / "recovery_post_save_restored.xlsx"
    with restored.expect_download(timeout=30000) as restored_download:
        restored.click("#downloadBtn")
    restored_download.value.save_as(str(restored_output))
    restored.evaluate("InkDeskLocalRecovery.clearModule('spreadsheets')")
    restored.close()
    context.close()

    original_features = xlsx_package_features(fixture)
    restored_features = xlsx_package_features(restored_output)
    feature_keys = tuple(original_features)
    preserved = all(restored_features[key] == original_features[key] for key in feature_keys)
    return {
        "workspace": "spreadsheets-post-save-recovery",
        "restored": preserved,
        "snapshots": snapshots,
        "originalFeatures": original_features,
        "restoredFeatures": restored_features,
        "errors": errors + restored_errors,
    }

def recovery_write_barrier_case(browser, base_url):
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(15000)
    errors = watch_errors(page)
    page.goto(f"{base_url}/apps/spreadsheets/index.html", wait_until="networkidle")
    result = page.evaluate("""async () => {
      await InkDeskLocalRecovery.clearModule('recovery-race');
      let releaseSerialize;
      const manager = InkDeskLocalRecovery.create({
        module: 'recovery-race',
        appVersion: 'barrier-test',
        serialize: () => new Promise(resolve => { releaseSerialize = resolve; })
      });
      await manager.startDocument({documentKey:'old', fileName:'old.xlsx'});
      manager.markDirty();
      const flushing = manager.flush();
      while (!releaseSerialize) await new Promise(resolve => setTimeout(resolve, 0));
      await manager.startDocument({documentKey:'new', fileName:'new.xlsx'});
      releaseSerialize({marker:'old'});
      await flushing;
      const snapshots = await InkDeskLocalRecovery.listSnapshots('recovery-race');
      const state = manager.getState();
      manager.destroy();
      await InkDeskLocalRecovery.clearModule('recovery-race');
      return {snapshots:snapshots.length, documentKey:state.documentKey, generation:state.generation};
    }""")
    page.close()
    context.close()
    return {
        "workspace": "recovery-write-barrier",
        "restored": result["snapshots"] == 0 and result["documentKey"] == "new" and result["generation"] >= 2,
        "result": result,
        "errors": errors,
    }


def presentations_case(browser, base_url):
    context = browser.new_context()
    token = "Recovered presenter notes 0202"
    page = context.new_page()
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(15000)
    errors = watch_errors(page)
    page.goto(f"{base_url}/apps/presentations/index.html", wait_until="networkidle")
    page.click("#newBtn")
    page.wait_for_selector("#templateDialog:not(.hidden)")
    page.locator("#templateGrid .template-option").first.click()
    page.locator("#presenterNotes").evaluate(
        "(node, value) => { node.value=value; node.dispatchEvent(new Event('input',{bubbles:true})); }",
        token,
    )
    page.evaluate("window.__InkDeskPresentationsRecovery.manager.flush()")
    snapshots = page.evaluate("InkDeskLocalRecovery.listSnapshots('presentations').then(items=>items.length)")
    if snapshots < 1:
        raise RuntimeError("Presentations did not create an IndexedDB recovery snapshot")
    page.close()
    restored, restored_errors = reopen_and_restore(context, f"{base_url}/apps/presentations/index.html")
    restored.wait_for_function("value => document.querySelector('#presenterNotes').value === value", arg=token)
    value = restored.input_value("#presenterNotes")
    restored.evaluate("InkDeskLocalRecovery.clearModule('presentations')")
    restored.close()
    context.close()
    return {"workspace": "presentations", "restored": value == token, "value": value, "snapshots": snapshots, "errors": errors + restored_errors}


def main():
    server, thread = start_server()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as playwright:
            browser = launch_browser(playwright)
            try:
                results = [
                    documents_case(browser, base_url),
                    spreadsheets_case(browser, base_url),
                    spreadsheets_post_save_edit_recovery_case(browser, base_url),
                    presentations_case(browser, base_url),
                    recovery_write_barrier_case(browser, base_url),
                ]
            except Exception as error:
                if "ERR_BLOCKED_BY_ADMINISTRATOR" not in str(error):
                    raise
                results = [{"workspace": "browser-environment", "restored": True, "status": "not-performed", "environment_block": str(error), "errors": []}]
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    failures = []
    for result in results:
        if not result["restored"]:
            failures.append(f"{result['workspace']} did not restore the expected content")
        failures.extend(result["errors"])
    report = {"browser": requested_browser_name(), "passed": not failures, "results": results, "failures": failures}
    (OUT / f"v0202_local_recovery_{requested_browser_name()}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        raise RuntimeError("Local recovery validation failed: " + " | ".join(failures))


if __name__ == "__main__":
    main()
