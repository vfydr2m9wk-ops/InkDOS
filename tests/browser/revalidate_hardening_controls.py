"""Behavioral browser checks for lifecycle, DOCX DOM sanitization, formula and XML guards."""
from __future__ import annotations
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

from browser_support import launch_browser

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")


def main():
    requests=[]
    with sync_playwright() as playwright:
        browser=launch_browser(playwright)
        page=browser.new_page()
        page.on("request", lambda request: requests.append(request.url))
        page.set_content("<!doctype html><html><body><div id='target'></div></body></html>")
        for rel in ("shared/office-runtime.js","shared/file-lifecycle.js","shared/formula-engine.js","shared/safe-dom.js"):
            page.add_script_tag(path=str(ROOT/rel))
        result=page.evaluate(r"""async () => {
          window.__hostileExecuted=0;
          const hostile=`<p id="location" name="cookie" onclick="window.__hostileExecuted=1" style="background-image:url(https://attacker.invalid/a);color:#123456">Safe text</p>
            <img src="javascript:alert(1)" onerror="window.__hostileExecuted=2"><svg><foreignObject><iframe srcdoc="<script>window.__hostileExecuted=3<\\/script>"></iframe></foreignObject></svg>
            <a href="javascript:alert(4)">link text</a><span style="width:10px;expression(alert(5))">span</span>`;
          InkDeskSafeDOM.appendSanitizedHtml(document.querySelector('#target'),hostile);
          await new Promise(resolve=>setTimeout(resolve,50));
          const target=document.querySelector('#target');
          const attrs=[...target.querySelectorAll('*')].flatMap(el=>[...el.attributes].map(a=>a.name+'='+a.value));
          const lifecycle=InkDeskFileLifecycle.create();lifecycle.markDirty();lifecycle.beginExport();lifecycle.downloadRequested({fileName:'copy.docx',bytes:10});
          let doctypeRejected=false,depthRejected=false,downloadRejected=false;
          try{InkDeskRuntime.parseXml('<!DOCTYPE x [<!ENTITY e "x">]><x>&e;</x>','hostile.xml')}catch(_){doctypeRejected=true}
          try{InkDeskRuntime.parseXml('<a>'.repeat(140)+'</a>'.repeat(140),'deep.xml')}catch(_){depthRejected=true}
          const originalClick=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){throw new Error('blocked')};
          try{InkDeskRuntime.requestDownload(new Blob(['x']),'copy.docx')}catch(_){downloadRejected=true}finally{HTMLAnchorElement.prototype.click=originalClick}
          let injectionRejected=false;try{InkDeskFormula.evaluateArithmetic('1;window.__hostileExecuted=9')}catch(_){injectionRejected=true}
          return {
            hostileExecuted:window.__hostileExecuted,
            html:target.innerHTML,
            attrs,
            hasActiveElement:!!target.querySelector('script,iframe,svg,foreignObject,a'),
            hasUnsafeUrl:attrs.some(x=>/javascript:|https:\/\/attacker|url\s*\(|srcdoc|^on/i.test(x)),
            lifecycleState:lifecycle.state,
            warns:lifecycle.shouldWarnBeforeUnload(),
            doctypeRejected,depthRejected,downloadRejected,injectionRejected,
            formula:InkDeskFormula.evaluateArithmetic('(2+3)*4')
          };
        }""")
        browser.close()
    problems=[]
    if result["hostileExecuted"] != 0: problems.append("hostile DOM executed")
    if result["hasActiveElement"]: problems.append("active element survived")
    if result["hasUnsafeUrl"]: problems.append("unsafe URL/attribute survived")
    if not result["warns"] or result["lifecycleState"]!="download-requested-unverified": problems.append("download cleared lifecycle warning")
    for key in ("doctypeRejected","depthRejected","downloadRejected","injectionRejected"):
        if not result[key]: problems.append(f"{key} was false")
    if result["formula"] != 20: problems.append("formula precedence failed")
    external=[url for url in requests if "attacker.invalid" in url]
    if external: problems.append("hostile DOM initiated network request")
    if problems: raise RuntimeError("Hardening controls failed: "+" | ".join(problems))
    report={"result":result,"unexpected_network_requests":external}
    (OUT/"hardening_controls.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__ == "__main__":
    main()
