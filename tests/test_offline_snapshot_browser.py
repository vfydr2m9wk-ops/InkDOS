#!/usr/bin/env python3
"""Real worker lifecycle: waiting update, partial deploy rejection, offline revision."""
import functools,json,os,re,sys,tempfile,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_offline_snapshot import render
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def end_headers(self):
        self.send_header('Cache-Control','no-store');super().end_headers()
def main():
    with tempfile.TemporaryDirectory(prefix='inkdos-snapshot-') as td:
        root=Path(td)
        template=(ROOT/'service-worker.js').read_text()
        template=re.sub(r'const APP_SHELL=\[.*?\];','const APP_SHELL=["./index.html","./app.js","./VERSION.json"];',template,flags=re.S)
        (root/'VERSION.json').write_text('{"version":"2.5.2"}')
        (root/'index.html').write_text("<html><head><title>Snapshot probe</title></head><body><script>navigator.serviceWorker.register('./service-worker.js',{updateViaCache:'none'});</script></body></html>")
        def revision(code):
            (root/'app.js').write_text(code)
            (root/'service-worker.js').write_text(render(root,template))
        revision('snapshot-A')
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=td))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        base=f'http://127.0.0.1:{server.server_port}/'
        try:
            with sync_playwright() as p:
                browser=getattr(p,os.environ.get('BROWSER','chromium')).launch()
                ctx=browser.new_context(service_workers='allow');page=ctx.new_page()
                page.goto(base);page.evaluate('async()=>{await navigator.serviceWorker.ready}')
                page.reload();page.wait_for_function('navigator.serviceWorker.controller!==null')
                read=lambda:page.evaluate("async()=>await (await fetch('./app.js')).text()")
                assert read()=='snapshot-A'
                # New worker describes B while the server serves corrupt bytes.
                revision('snapshot-B');(root/'app.js').write_text('incomplete-deployment')
                state=page.evaluate("""async()=>{const r=await navigator.serviceWorker.getRegistration();const done=new Promise(resolve=>r.addEventListener('updatefound',()=>{const w=r.installing;w.addEventListener('statechange',()=>{if(['installed','redundant'].includes(w.state))resolve(w.state)})},{once:true}));await r.update();return await Promise.race([done,new Promise((_,reject)=>setTimeout(()=>reject(Error('Worker update timed out')),30000))])}""")
                assert state=='redundant',state
                assert read()=='snapshot-A','failed install preserves active cache'
                # Successful C must wait while A's editor tab remains open.
                revision('snapshot-C')
                page.evaluate("async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update()}")
                page.wait_for_function("async()=>!!(await navigator.serviceWorker.getRegistration()).waiting")
                assert read()=='snapshot-A','open editor must remain on its own revision'
                await_activation=ctx.new_page();await_activation.goto('about:blank')
                page.close()
                # No clients of the old worker remain. The next navigation can use C.
                page=ctx.new_page();page.goto(base)
                page.wait_for_function("async()=>!(await navigator.serviceWorker.getRegistration()).waiting")
                page.reload();assert read()=='snapshot-C'
                ctx.set_offline(True);page.reload();assert read()=='snapshot-C'
                assert page.title()=='Snapshot probe'
                browser.close()
                print('Browser snapshot lifecycle, partial install rollback and offline revision: PASS')
        finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
