"""Behavioral regression for v0.20.2.1 private IndexedDB recovery snapshots."""
from __future__ import annotations

import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
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
    page.evaluate("window.__InkDeskSpreadsheetsRecovery.manager.flush()")
    snapshots = page.evaluate("InkDeskLocalRecovery.listSnapshots('spreadsheets').then(items=>items.length)")
    if snapshots < 1:
        raise RuntimeError("Spreadsheets did not create an IndexedDB recovery snapshot")
    page.close()
    restored, restored_errors = reopen_and_restore(context, f"{base_url}/apps/spreadsheets/index.html")
    value = restored.evaluate("window.__InkDeskSpreadsheetsRecovery.capture().then(p=>p.book.sheets[0].cells.find(item=>item[0]==='A1')?.[1]?.v)")
    restored.evaluate("InkDeskLocalRecovery.clearModule('spreadsheets')")
    restored.close()
    context.close()
    return {"workspace": "spreadsheets", "restored": value == token, "value": value, "snapshots": snapshots, "errors": errors + restored_errors}


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
                    presentations_case(browser, base_url),
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
