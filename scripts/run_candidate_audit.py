#!/usr/bin/env python3
"""Serve exact checked-out candidate; never audit published baseline as candidate."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def end_headers(self):self.send_header('Cache-Control','no-store');super().end_headers()
def main():
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    expected=os.environ.get('INKDOS_EXPECTED_SHA',sha)
    if sha!=expected:raise SystemExit(f'Candidate SHA mismatch: {sha} != {expected}')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip():raise SystemExit('Candidate tracked files are dirty')
    browser=os.environ.get('INKDOS_AUDIT_BROWSER','chromium')
    out=ROOT/'artifacts'/f'candidate-{browser}';out.mkdir(parents=True,exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    env=dict(os.environ,INKDOS_ONLINE_BASE=f'http://127.0.0.1:{server.server_port}/',INKDOS_AUDIT_OUT=str(out/'visual'),INKDOS_STATEFUL_OUT=str(out/'stateful'),BROWSER=browser)
    (out/'provenance.json').write_text(json.dumps({'commit':sha,'browser':browser,'candidateOnly':True,'serviceWorkerSha256':hashlib.sha256((ROOT/'service-worker.js').read_bytes()).hexdigest()},indent=2))
    try:
        subprocess.run([sys.executable,'tests/test_offline_snapshot_browser.py'],cwd=ROOT,env=env,check=True)
        subprocess.run([sys.executable,'tests/test_online_pages_visual_matrix_browser.py'],cwd=ROOT,env=env,check=True)
        report=json.loads((out/'visual/report.json').read_text());summary=report['summary']
        gates=['matrixExceptions','httpFailures','casesWithJsErrors','clickExceptions']
        if any(summary[k] for k in gates):raise SystemExit('Candidate matrix failures: '+json.dumps(summary))
        if browser=='chromium':
            subprocess.run([sys.executable,'tests/test_online_stateful_control_surfaces_browser.py'],cwd=ROOT,env=env,check=True)
            report=json.loads((out/'stateful/report.json').read_text())
            summary=report['summary']
            print('Stateful summary:',json.dumps(summary))
            if summary['appsWithJsErrors'] or summary['surfaceFailures']:raise SystemExit('Candidate stateful controls failed')
    finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
