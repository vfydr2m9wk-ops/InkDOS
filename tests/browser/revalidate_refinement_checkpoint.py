#!/usr/bin/env python3
from __future__ import annotations
import json, os, re
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_support import launch_browser
ROOT=Path(__file__).resolve().parents[2]
RESULT=ROOT/'tests/browser/results/refinement_checkpoint.json'
APPS=('documents','spreadsheets','presentations','pdf','txt','epub')
def source(path):return (ROOT/path).read_text(encoding='utf-8')
def strip(html):
    html=re.sub(r'<link\b[^>]*>','',html,flags=re.I)
    return re.sub(r'<script\b[^>]*>.*?</script>','',html,flags=re.S|re.I)
def storage(page):
    page.evaluate("""() => {const m=new Map();Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k),clear:()=>m.clear()}})}""")
def inject_core(page,app_home=False):
    storage(page);page.add_style_tag(content=source('shared/ui/app-shell.css'));page.add_style_tag(content=source('shared/ui/refinement-home.css'));page.add_style_tag(content=source('shared/ui/app-home.css'))
    for path in ('shared/product-config.js','modules/module-registry.js','modules/module-loader.js','shared/recent-files.js','shared/file-router.js','shared/app-shell.js'):
        page.add_script_tag(content=source(path))
    if app_home:page.add_script_tag(content=source('shared/app-home.js'))
def main():
    with sync_playwright() as pw:
        browser=launch_browser(pw);page=browser.new_page(viewport={'width':390,'height':844})
        page.set_content(strip(source('index.html')),wait_until='load');inject_core(page);page.add_script_tag(content=source('shared/suite-shell.js'));page.wait_for_function("() => Boolean(window.InkDOSSuite)")
        assert page.locator('.hub-intro').count()==0 and page.locator('.workspace-grid').count()==0
        assert page.locator('[data-recent-filter]').count()==7
        assert page.locator('[data-app-launcher-trigger]').count()==1
        page.locator('[data-app-launcher-trigger]').click();assert page.locator('.inkdos-app-launcher-item').count()==6;page.keyboard.press('Escape')
        assert not page.locator('[data-recent-clear]').is_visible()
        page.evaluate("""() => {InkDOSRecentFiles.registerCreated({appId:'documents',name:'Report.docx',extension:'docx'});InkDOSSuite.renderRecent()}""")
        assert page.locator('.recent-row').count()==1 and page.locator('[data-recent-clear]').is_visible()
        widths=(320,360,375,390,412,430,768,1024,1280,1440)
        for width in widths:
            page.set_viewport_size({'width':width,'height':800});assert page.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1")
        app_results={}
        for app in APPS:
            html=strip(source(f'apps/{app}/index.html'));page.set_content(html,wait_until='load');page.add_style_tag(content=source('shared/ui/app-shell.css'));page.add_style_tag(content=source('shared/ui/app-home.css'));inject_core(page,app_home=True);page.wait_for_function("() => Boolean(document.querySelector('.inkdos-app-home-page'))")
            creates=page.locator('[data-app-home-action="create"]').count();opens=page.locator('[data-app-home-action="open"]').count();assert opens==1;assert creates==(0 if app in {'pdf','epub'} else 1);assert page.locator('.inkdos-app-launcher-item').count()==6
            app_results[app]={'create':creates,'open':opens}
        payload={'browser':os.environ.get('INKDOS_BROWSER','chromium'),'home_widths':list(widths),'apps':app_results}
        RESULT.parent.mkdir(parents=True,exist_ok=True);RESULT.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8');browser.close();print(json.dumps(payload,indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
