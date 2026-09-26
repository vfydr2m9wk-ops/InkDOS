#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, tempfile, time
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get("INKDOS_ONLINE_BASE","https://vfydr2m9wk-ops.github.io/InkDOS/").rstrip("/")+"/"
BROWSER_NAME=os.environ.get("INKDOS_AUDIT_BROWSER","chromium").strip().lower()
OUT=Path(os.environ.get("INKDOS_SURFACE_OUT",f"audit-online-surfaces-{BROWSER_NAME}"))
OUT.mkdir(parents=True,exist_ok=True)

spec=importlib.util.spec_from_file_location("stateful",ROOT/"tests/test_online_stateful_control_surfaces_browser.py")
stateful=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(stateful)
APPS={k:v for k,v in stateful.PAGES.items() if k!="home"}
SURFACES=stateful.SURFACES

def visible_surface_count(page):
    return page.evaluate("""()=>[...document.querySelectorAll(
      '.drawer,.context-drawer,.zoom-popover,.navigation-panel,.toc-panel,.search-panel,.appearance-popover,[role="dialog"],[role="menu"]'
    )].filter(el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return !el.hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0}).length""")

def tokens(page):
    return page.evaluate("""()=>{const r=document.documentElement,s=getComputedStyle(r);const btn=[...document.querySelectorAll('button')].find(b=>{const q=getComputedStyle(b),x=b.getBoundingClientRect();return !b.hidden&&q.display!=='none'&&x.width>0&&x.height>0});const bs=btn?getComputedStyle(btn):null;return {
      resolved:r.dataset.appearanceResolved||r.dataset.appearance||r.dataset.theme||null,
      bg:s.getPropertyValue('--bg').trim(),chrome:s.getPropertyValue('--chrome').trim(),text:s.getPropertyValue('--text').trim(),
      muted:s.getPropertyValue('--muted').trim(),line:s.getPropertyValue('--line').trim(),accent:s.getPropertyValue('--accent').trim(),
      sampleButton:btn?{id:btn.id||null,w:Math.round(btn.getBoundingClientRect().width),h:Math.round(btn.getBoundingClientRect().height),
        radius:bs.borderRadius,border:bs.borderColor,background:bs.backgroundColor,color:bs.color}:null};}""")

def main():
    report={"base":BASE,"browser":BROWSER_NAME,"themes":{},"homeRoutes":{},"errors":[]}
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); fixtures={"pdf":td/"audit.pdf","epub":td/"audit.epub"}
        stateful.minimal_pdf(fixtures["pdf"]); stateful.minimal_epub(fixtures["epub"])
        with sync_playwright() as pw:
            browser=getattr(pw,BROWSER_NAME).launch(headless=True)
            for theme in ("light","dark"):
                report["themes"][theme]={}
                for app,path in APPS.items():
                    report["themes"][theme][app]={"initial":None,"surfaces":[]}
                    ctx=browser.new_context(viewport={"width":1440,"height":900},color_scheme=theme,service_workers="block",accept_downloads=True)
                    ctx.add_init_script(f"""(()=>{{try{{localStorage.setItem('inkdos2:appearance',{json.dumps(theme)});localStorage.setItem('inkdos2:ui-density','desktop')}}catch(_){{}}}})();""")
                    page=ctx.new_page(); errors=[]
                    page.on("pageerror",lambda exc,e=errors:e.append("pageerror: "+str(exc)))
                    page.on("console",lambda msg,e=errors:e.append("console-error: "+msg.text) if msg.type=="error" else None)
                    page.on("dialog",lambda d:d.dismiss())
                    page.goto(urljoin(BASE,path),wait_until="load",timeout=30000); page.wait_for_timeout(180)
                    shot=OUT/theme/app/"direct.png"; shot.parent.mkdir(parents=True,exist_ok=True); page.screenshot(path=str(shot))
                    report["themes"][theme][app]["initial"]={"tokens":tokens(page),"screenshot":str(shot.relative_to(OUT))}
                    ctx.close()
                    for label,selector in SURFACES.get(app,[]):
                        ctx=browser.new_context(viewport={"width":1440,"height":900},color_scheme=theme,service_workers="block",accept_downloads=True)
                        ctx.add_init_script(f"""(()=>{{try{{localStorage.setItem('inkdos2:appearance',{json.dumps(theme)});localStorage.setItem('inkdos2:ui-density','desktop')}}catch(_){{}}}})();""")
                        page=ctx.new_page(); errs=[]
                        page.on("pageerror",lambda exc,e=errs:e.append("pageerror: "+str(exc)))
                        page.on("console",lambda msg,e=errs:e.append("console-error: "+msg.text) if msg.type=="error" else None)
                        page.on("dialog",lambda d:d.dismiss())
                        page.goto(urljoin(BASE,path),wait_until="load",timeout=30000); page.wait_for_timeout(120)
                        stateful.prepare_active(app,page,fixtures); page.wait_for_timeout(120)
                        loc=page.locator(selector).first
                        status="missing"
                        if loc.count():
                            if loc.is_enabled() and loc.is_visible():
                                loc.click(no_wait_after=True,timeout=3000); page.wait_for_timeout(220); status="clicked"
                            else: status="disabled-or-hidden"
                        safe=label.replace("/","-").replace(" ","-")
                        shot=OUT/theme/app/f"surface-{safe}.png"; page.screenshot(path=str(shot))
                        row={"label":label,"selector":selector,"status":status,"visibleSurfaces":visible_surface_count(page),
                             "tokens":tokens(page),"screenshot":str(shot.relative_to(OUT)),"errors":errs}
                        report["themes"][theme][app]["surfaces"].append(row)
                        report["errors"].extend([f"{theme}/{app}/{label}: {x}" for x in errs])
                        ctx.close()
                report["homeRoutes"][theme]={}
                for app,path in APPS.items():
                    ctx=browser.new_context(viewport={"width":1440,"height":900},color_scheme=theme,service_workers="block")
                    ctx.add_init_script(f"""(()=>{{try{{localStorage.setItem('inkdos2:appearance',{json.dumps(theme)});localStorage.setItem('inkdos2:ui-density','desktop')}}catch(_){{}}}})();""")
                    page=ctx.new_page(); errs=[]
                    page.on("pageerror",lambda exc,e=errs:e.append("pageerror: "+str(exc)))
                    page.on("console",lambda msg,e=errs:e.append("console-error: "+msg.text) if msg.type=="error" else None)
                    page.goto(BASE,wait_until="load",timeout=30000)
                    href=f"./apps/{app}/index.html"
                    link=page.locator(f'a.workspace-card[href^="{href}"]').first
                    if link.count()!=1: raise AssertionError((theme,app,"home link missing"))
                    link.click(); page.wait_for_load_state("load"); page.wait_for_timeout(180)
                    if f"/apps/{app}/index.html" not in page.url or "suite=1" not in page.url: raise AssertionError((theme,app,page.url))
                    shot=OUT/theme/app/"via-home.png"; page.screenshot(path=str(shot))
                    report["homeRoutes"][theme][app]={"url":page.url,"tokens":tokens(page),"screenshot":str(shot.relative_to(OUT)),"errors":errs}
                    report["errors"].extend([f"{theme}/home->{app}: {x}" for x in errs])
                    ctx.close()
            browser.close()
    (OUT/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if report["errors"]: raise SystemExit("Visual surface audit found JS/console errors; see report.json")
    print(json.dumps({"browser":BROWSER_NAME,"themes":list(report["themes"]),"homeRoutes":sum(len(v) for v in report["homeRoutes"].values()),"errors":0},indent=2))
if __name__=="__main__": main()
