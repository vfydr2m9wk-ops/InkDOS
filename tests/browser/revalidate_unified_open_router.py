"""Validate unified file routing, origin-bound bridge transfer, and home links."""
from __future__ import annotations

import json
import time
from urllib.parse import urlparse
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
    trusted_base = "https://trusted.inkdesk.test"
    hostile_base = "https://hostile.inkdesk.test"
    child_html = """<!doctype html><meta charset=\"utf-8\"><script src=\"/shared/file-router.js\"></script>
<script>
window.__openedFile='';
InkDeskFileRouter.attachWorkspace({extensions:['docx'],openFile:file=>{window.__openedFile=file.name;}});
</script>"""
    hostile_html = """<!doctype html><meta charset=\"utf-8\"><script>
const params=new URLSearchParams(location.search);
setTimeout(()=>{
  parent.frames[0].postMessage({type:'inkdesk:open-file',version:1,token:params.get('token'),expiresAt:Number(params.get('expires')),file:new File(['hostile'],'hostile.docx')},params.get('target'));
},50);
</script>"""
    router_source = (ROOT / "shared" / "file-router.js").read_text(encoding="utf-8")
    context = browser.new_context()

    def fulfill(route):
        parsed = urlparse(route.request.url)
        if parsed.hostname == "trusted.inkdesk.test" and parsed.path == "/shared/file-router.js":
            route.fulfill(status=200, content_type="application/javascript", body=router_source)
        elif parsed.hostname == "trusted.inkdesk.test" and parsed.path == "/bridge-child.html":
            route.fulfill(status=200, content_type="text/html", body=child_html)
        elif parsed.hostname == "hostile.inkdesk.test" and parsed.path == "/bridge-hostile.html":
            route.fulfill(status=200, content_type="text/html", body=hostile_html)
        else:
            route.fulfill(status=200, content_type="text/html", body="<!doctype html><meta charset='utf-8'><title>bridge host</title>")

    context.route("https://trusted.inkdesk.test/**", fulfill)
    context.route("https://hostile.inkdesk.test/**", fulfill)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        page.goto(trusted_base + "/bridge-host.html", wait_until="domcontentloaded")
    except Exception as error:
        if "ERR_BLOCKED_BY_ADMINISTRATOR" not in str(error):
            context.close()
            raise
        context.close()
        fallback = browser.new_page()
        fallback.set_content("<!doctype html><title>origin policy fallback</title>")
        fallback.add_script_tag(path=str(ROOT / "shared" / "file-router.js"))
        result = fallback.evaluate(
            """()=>{
            const trusted=InkDeskFileRouter._test.bridgeOriginPolicy('https://trusted.inkdesk.test/workspace');
            const opaque=InkDeskFileRouter._test.bridgeOriginPolicy('file:///InkDesk/workspace.html');
            return {
              trustedTarget:trusted.targetOrigin,
              trustedAccepted:InkDeskFileRouter._test.eventMatchesPolicy({origin:'https://trusted.inkdesk.test'},trusted),
              hostileRejected:!InkDeskFileRouter._test.eventMatchesPolicy({origin:'https://hostile.inkdesk.test'},trusted),
              opaqueAccepted:InkDeskFileRouter._test.eventMatchesPolicy({origin:'null'},opaque)
            };
            }"""
        )
        fallback.close()
        if not all((result["trustedAccepted"], result["hostileRejected"], result["opaqueAccepted"])):
            raise RuntimeError(f"Origin-policy fallback failed: {result}")
        return {
            "fullTwoOriginExecuted": False,
            "limitation": "Browser policy blocked synthetic HTTP(S) navigation; exact trusted/hostile origin policy was executed directly.",
            **result,
        }
    token = "bridge-test-token"
    expires = int(time.time() * 1000) + 15_000
    page.evaluate(
        """({trustedBase,hostileBase,token,expires})=>{
        const workspace=document.createElement('iframe');
        workspace.id='workspace';
        workspace.name='workspace';
        workspace.src=trustedBase+'/bridge-child.html?embedded=1&bridge='+encodeURIComponent(token)+'&bridgeVersion=1&bridgeExpires='+expires;
        document.body.appendChild(workspace);
        const hostile=document.createElement('iframe');
        hostile.id='hostile';
        hostile.src=hostileBase+'/bridge-hostile.html?token='+encodeURIComponent(token)+'&expires='+expires+'&target='+encodeURIComponent(trustedBase);
        document.body.appendChild(hostile);
        window.__bridgeReady=false;
        window.addEventListener('message',event=>{
          if(event.source!==workspace.contentWindow||event.origin!==trustedBase)return;
          if(event.data&&event.data.type==='inkdesk:workspace-ready'&&event.data.token===token){
            window.__bridgeReady=true;
            setTimeout(()=>workspace.contentWindow.postMessage({type:'inkdesk:open-file',version:1,token,expiresAt:expires,file:new File(['trusted'],'trusted.docx',{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})},trustedBase),500);
          }
        });
        }""",
        {"trustedBase": trusted_base, "hostileBase": hostile_base, "token": token, "expires": expires},
    )
    page.wait_for_function("window.__bridgeReady === true")
    child = page.frames[1]
    page.wait_for_timeout(250)
    before_trusted = child.evaluate("window.__openedFile")
    if before_trusted:
        raise RuntimeError(f"A hostile frame injected a file before the trusted parent: {before_trusted}")
    child.wait_for_function("window.__openedFile === 'trusted.docx'")
    opened = child.evaluate("window.__openedFile")
    if errors:
        raise RuntimeError("Bridge browser errors: " + " | ".join(errors))
    context.close()
    return {"fullTwoOriginExecuted": True, "opened": opened, "hostileInjectionRejected": before_trusted == "", "trustedOrigin": trusted_base, "hostileOrigin": hostile_base}


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
            "embeddedBridge": validate_embedded_bridge(browser),
            "homeLinks": validate_home_links(browser),
        }
        browser.close()
    (OUT / "unified_open_router.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Unified routing, origin-bound embedded transfer, hostile-origin rejection, and workspace home links passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
