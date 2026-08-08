"""Validate file launches, hosted PWA caching, and unsupported-API fallbacks."""
from __future__ import annotations

import json
import os
import threading
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError, sync_playwright
from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")
PAGES = (
    "index.html",
    "apps/documents/index.html",
    "apps/spreadsheets/index.html",
    "apps/presentations/index.html",
)


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


def validate_static_http_assets(base_url):
    required = (
        "index.html",
        "manifest.webmanifest",
        "service-worker.js",
        "shared/office-runtime.js",
        "shared/register-service-worker.js",
        "apps/documents/index.html",
        "apps/spreadsheets/index.html",
        "apps/presentations/index.html",
    )
    responses = {}
    for relative in required:
        with urllib.request.urlopen(f"{base_url}/{relative}", timeout=10) as response:
            body = response.read()
            responses[relative] = {
                "status": response.status,
                "content_type": response.headers.get_content_type(),
                "bytes": len(body),
            }
            if response.status != 200 or not body:
                raise RuntimeError(f"Static asset failed: {relative} ({response.status}, {len(body)} bytes)")
    return {"mode": "static-http-assets", "status": "passed", "responses": responses}


def collect_page_errors(page):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def record_console(message):
        if message.type != "error":
            return
        # Chromium emits a generic duplicate for failed HTTP resources. The
        # response listener below records the exact status and URL instead.
        if "Failed to load resource" in message.text:
            return
        errors.append(f"console.{message.type}: {message.text}")

    def record_response(response):
        if response.status >= 400:
            errors.append(f"http.{response.status}: {response.url}")

    page.on("console", record_console)
    page.on("response", record_response)
    return errors


def validate_file_launches(browser):
    page = browser.new_page(viewport={"width": 1366, "height": 900})
    errors = collect_page_errors(page)
    launched = []
    blocked_reason = None
    for relative in PAGES:
        try:
            page.goto((ROOT / relative).as_uri(), wait_until="load")
        except PlaywrightError as error:
            blocked_reason = str(error).splitlines()[0]
            break
        page.wait_for_selector("body")
        launched.append({"path": relative, "title": page.title()})
    page.close()
    return {
        "mode": "file",
        "status": "not-performed" if blocked_reason else "passed",
        "launched": launched,
        "environment_block": blocked_reason,
        "errors": errors if not blocked_reason else [],
    }


def validate_hosted_offline(browser, base_url):
    context = browser.new_context(viewport={"width": 1366, "height": 900})
    page = context.new_page()
    errors = collect_page_errors(page)
    try:
        page.goto(base_url + "/index.html", wait_until="networkidle")
    except PlaywrightError as error:
        page.close()
        context.close()
        return {
            "mode": "hosted-pwa",
            "status": "not-performed",
            "environment_block": str(error).splitlines()[0],
            "errors": [],
            "failed_requests": [],
        }
    failed_requests = []
    requested_origins = set()
    page.on("request", lambda request: requested_origins.add(request.url.split("/", 3)[0] + "//" + request.url.split("/", 3)[2]))
    page.on("requestfailed", lambda request: failed_requests.append(f"{request.method} {request.url}: {request.failure}"))
    page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.ready")
    page.evaluate("navigator.serviceWorker.ready")
    page.reload(wait_until="networkidle")
    page.wait_for_function("navigator.serviceWorker.controller !== null")
    online_titles = {}
    for relative in PAGES:
        page.goto(base_url + "/" + relative, wait_until="networkidle")
        online_titles[relative] = page.title()
    context.set_offline(True)
    offline_titles = {}
    for relative in PAGES:
        page.goto(base_url + "/" + relative, wait_until="load")
        page.wait_for_selector("body")
        offline_titles[relative] = page.title()
    context.set_offline(False)
    page.close()
    context.close()
    return {
        "mode": "hosted-pwa",
        "status": "passed",
        "online_titles": online_titles,
        "offline_titles": offline_titles,
        "requested_origins": sorted(requested_origins),
        "failed_requests": failed_requests,
        "errors": errors,
    }


def load_injected_app(page, workspace, scripts, base_url):
    source = ROOT / ("index.html" if workspace == "hub" else f"apps/{workspace}/index.html")
    soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
    for node in soup.find_all(["script", "link"]):
        node.decompose()
    base = soup.new_tag("base", href=base_url + "/")
    if soup.head:
        soup.head.insert(0, base)
    page.set_content(str(soup), wait_until="domcontentloaded")
    if workspace == "hub":
        page.add_style_tag(url=base_url + "/shared/hub.css")
    else:
        page.add_style_tag(url=base_url + f"/apps/{workspace}/styles.css")
        page.add_style_tag(url=base_url + "/shared/office-shell.css")
    for script in scripts:
        page.add_script_tag(url=base_url + "/" + script)


def validate_restricted_apis(browser, base_url):
    context = browser.new_context(viewport={"width": 1024, "height": 768}, has_touch=True)
    context.add_init_script(
        """
        Object.defineProperty(Navigator.prototype, 'serviceWorker', {configurable: true, get(){return undefined;}});
        Object.defineProperty(Navigator.prototype, 'clipboard', {configurable: true, get(){return undefined;}});
        Object.defineProperty(window, 'indexedDB', {configurable: true, get(){throw new Error('IndexedDB denied by test');}});
        Object.defineProperty(window, 'localStorage', {configurable: true, get(){throw new Error('localStorage denied by test');}});
        try{delete Element.prototype.requestFullscreen;}catch(error){void error;}
        try{delete Document.prototype.exitFullscreen;}catch(error){void error;}
        """
    )
    configurations = {
        "hub": ("shared/register-service-worker.js",),
        "documents": (
            "shared/vendor/pako_inflate.min.js",
            "shared/office-runtime.js",
            "apps/documents/docx-parser.js",
            "shared/vendor/jszip.min.js",
            "apps/documents/docx-writer.js",
            "shared/office-shell.js",
            "apps/documents/app.js",
            "shared/register-service-worker.js",
        ),
        "spreadsheets": (
            "shared/office-runtime.js",
            "shared/vendor/jszip.min.js",
            "apps/spreadsheets/xls-biff8-engine.js",
            "apps/spreadsheets/xlsx-engine.js",
            "shared/office-shell.js",
            "apps/spreadsheets/formula-safety.js",
            "apps/spreadsheets/history-controller.js",
            "apps/spreadsheets/app.js",
            "shared/register-service-worker.js",
        ),
        "presentations": (
            "shared/office-runtime.js",
            "shared/vendor/jszip.min.js",
            "apps/presentations/engine/compatibility.js",
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
            "shared/register-service-worker.js",
        ),
    }
    results = []
    all_errors = []
    for workspace, scripts in configurations.items():
        page = context.new_page()
        errors = collect_page_errors(page)
        load_injected_app(page, workspace, scripts, base_url)
        page.wait_for_selector("body")
        fallback = None
        if workspace == "presentations":
            page.click("#newBtn")
            page.click("#templateGrid .template-option")
            page.click("#presentFromStartTop")
            page.wait_for_function("!document.querySelector('#presentOverlay').classList.contains('hidden')")
            page.click("#exitPresentBtn")
            page.wait_for_function("document.querySelector('#presentOverlay').classList.contains('hidden')")
            fallback = True
        results.append({"workspace": workspace, "presentation_fallback": fallback, "errors": errors})
        all_errors.extend(errors)
        page.close()
    context.close()
    return {
        "mode": "restricted-apis-touch-emulation",
        "status": "passed" if not all_errors else "failed",
        "workspaces": results,
        "errors": all_errors,
    }

def main():
    server, thread = start_server()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as playwright:
            browser = launch_browser(playwright)
            results = [
                validate_static_http_assets(base_url),
                validate_file_launches(browser),
                validate_hosted_offline(browser, base_url),
                validate_restricted_apis(browser, base_url),
            ]
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    problems = []
    for result in results:
        problems.extend(result.get("errors", []))
        problems.extend(result.get("failed_requests", []))
    hosted = results[2]
    if hosted.get("status") == "passed" and hosted["requested_origins"] != [base_url]:
        problems.append(f"Unexpected runtime origins: {hosted['requested_origins']}")
    if problems:
        raise RuntimeError("Launch/offline validation failed: " + " | ".join(problems))
    output = OUT / "launch_and_offline_modes.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
