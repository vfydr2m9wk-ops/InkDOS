#!/usr/bin/env python3
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from browser_support import launch_browser

ROOT = Path(__file__).resolve().parents[2]

def text(rel): return (ROOT / rel).read_text(encoding="utf-8")
def shell_html(rel):
    soup = BeautifulSoup(text(rel), "html.parser")
    for node in soup.find_all("script"): node.decompose()
    for node in soup.find_all("link"): node.decompose()
    return str(soup)

def main():
    with sync_playwright() as pw:
        browser = launch_browser(pw)
        page = browser.new_page()
        page.set_content(shell_html("apps/txt/index.html"))
        for rel in ("shared/file-lifecycle.js", "apps/txt/history-controller.js", "apps/txt/find-controller.js"):
            page.add_script_tag(content=text(rel))
        page.add_script_tag(content=r'''window.__recoveryCalls=[];
window.InkDOSLocalRecovery={create(options){window.__txtRecoveryOptions=options;return {
 startDocument:async c=>window.__recoveryCalls.push(['start',c.fileName||'']),
 markDirty:()=>window.__recoveryCalls.push(['dirty']), flush:async()=>window.__recoveryCalls.push(['flush']),
 discardCurrent:async()=>window.__recoveryCalls.push(['discard']), cancelPrompt:()=>window.__recoveryCalls.push(['cancel']),
 updateFileName:n=>window.__recoveryCalls.push(['name',n]), promptLatest:()=>window.__recoveryCalls.push(['prompt'])
};}};''')
        page.add_script_tag(content=text("apps/txt/recovery-controller.js"))
        page.add_script_tag(content=text("apps/txt/app.js"))
        page.click("#newStartBtn")
        page.fill("#editor", "recover me")
        page.dispatch_event("#editor", "input")
        state = page.evaluate("() => ({calls:window.__recoveryCalls, hasOptions:!!window.__txtRecoveryOptions})")
        assert state["hasOptions"]
        assert any(c[0]=="start" for c in state["calls"]), state
        assert any(c[0]=="dirty" for c in state["calls"]), state
        page.evaluate(r'''async()=>window.__txtRecoveryOptions.restore({snapshot:{fileName:'Recovered.txt',payload:{text:'private recovery',fileName:'Recovered.txt',lineEnding:'\n',encoding:'UTF-8',workspaceZoom:100}}})''')
        restored=page.evaluate("() => ({text:document.querySelector('#editor').value,title:document.querySelector('#docTitle').value,status:document.querySelector('#statusText').textContent})")
        assert restored["text"]=="private recovery", restored
        assert restored["title"]=="Recovered.txt", restored
        assert "Recovered" in restored["status"], restored
        browser.close()
    print("TXT recovery integration passed.")
    return 0
if __name__ == '__main__': raise SystemExit(main())
