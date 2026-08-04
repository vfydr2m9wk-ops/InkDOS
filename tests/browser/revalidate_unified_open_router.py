"""Validate unified file routing, local-file bridge transfer, and home links."""
from __future__ import annotations

import json
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from browser_support import launch_browser

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)


def stripped_html(path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for node in soup.find_all(["script", "link"]):
        node.decompose()
    return str(soup)


def validate_hub_routes(browser):
    cases = (
        ("minimal.docx", "./apps/documents/index.html"),
        ("minimal.xlsx", "./apps/spreadsheets/index.html"),
        ("minimal.pptx", "./apps/presentations/index.html"),
    )
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(stripped_html(ROOT / "index.html"), wait_until="domcontentloaded")
    page.add_script_tag(path=str(ROOT / "shared" / "file-router.js"))
    page.add_script_tag(path=str(ROOT / "shared" / "hub-open.js"))
    if page.locator("#openAnyDocument").count() != 1:
        raise RuntimeError("The unified Open document button is missing.")
    results = []
    for fixture, expected in cases:
        page.set_input_files("#openAnyInput", str(ROOT / "tests" / "fixtures" / fixture))
        routed = page.evaluate("InkDeskFileRouter.routeForFile(document.getElementById('openAnyInput').files[0])")
        if routed["path"] != expected:
            raise RuntimeError(f"{fixture} routed to {routed['path']} instead of {expected}")
        results.append({"fixture": fixture, "path": routed["path"]})
    if errors:
        raise RuntimeError("Browser errors: " + " | ".join(errors))
    page.close()
    return results


def validate_embedded_bridge(browser):
    page = browser.new_page()
    page.set_content('<iframe id="workspace" src="about:blank?embedded=1&bridge=bridge-test"></iframe>')
    frame = page.frame_locator("#workspace")
    page.evaluate(
        """
        const iframe=document.getElementById('workspace');
        window.addEventListener('message',event=>{
          if(event.source!==iframe.contentWindow)return;
          if(event.data&&event.data.type==='inkdesk:workspace-ready'&&event.data.token==='bridge-test'){
            iframe.contentWindow.postMessage({type:'inkdesk:open-file',token:'bridge-test',file:new File(['test'],'bridge.docx',{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})},'*');
          }
        });
        """
    )
    child = page.frames[1]
    child.add_script_tag(path=str(ROOT / "shared" / "file-router.js"))
    child.evaluate(
        """
        window.__openedFile='';
        InkDeskFileRouter.attachWorkspace({extensions:['docx'],openFile:file=>{window.__openedFile=file.name;}});
        """
    )
    child.wait_for_function("window.__openedFile === 'bridge.docx'")
    opened = child.evaluate("window.__openedFile")
    page.close()
    return opened


def validate_home_links(browser):
    page = browser.new_page()
    results = {}
    for workspace in ("documents", "spreadsheets", "presentations"):
        page.set_content(stripped_html(ROOT / "apps" / workspace / "index.html"), wait_until="domcontentloaded")
        links = page.locator("a.home-link")
        if links.count() < 1:
            raise RuntimeError(f"Home link missing in {workspace}")
        first = links.first
        results[workspace] = {"href": first.get_attribute("href"), "target": first.get_attribute("target")}
        if results[workspace] != {"href": "../../index.html", "target": "_top"}:
            raise RuntimeError(f"Invalid home link in {workspace}: {results[workspace]}")
    page.close()
    return results


def main():
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        report = {
            "status": "passed",
            "hubRoutes": validate_hub_routes(browser),
            "embeddedBridgeFile": validate_embedded_bridge(browser),
            "homeLinks": validate_home_links(browser),
        }
        browser.close()
    (OUT / "unified_open_router.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Unified DOCX/XLSX/PPTX routing, embedded file transfer, and workspace home links passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
