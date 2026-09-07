#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
ACTIVE=('documents','spreadsheets','presentations','txt','epub','pdf')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def tree_digest(root,exclude=()):
    root=Path(root); ex=set(exclude); h=hashlib.sha256()
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        rel=p.relative_to(root).as_posix()
        if rel in ex: continue
        rb=rel.encode(); h.update(len(rb).to_bytes(4,'big')); h.update(rb); h.update(bytes.fromhex(sha(p)))
    return h.hexdigest()
def main():
    required=('index.html','VERSION.json','DEVELOPMENT_STATE.json','SOURCE_LOCK.json','manifest.webmanifest','service-worker.js','README.md','CHECKSUMS.sha256','scripts/apply_update_package.py')
    for rel in required:
        if not (ROOT/rel).is_file(): raise SystemExit(f'Required file missing: {rel}')
    v=json.loads((ROOT/'VERSION.json').read_text()); state=json.loads((ROOT/'DEVELOPMENT_STATE.json').read_text()); lock=json.loads((ROOT/'SOURCE_LOCK.json').read_text())
    if v.get('version')!='2.0.3': raise SystemExit('Unexpected version')
    if state.get('appliedSequence')!=71 or state.get('currentPackage')!='2.0.3-pdf-final': raise SystemExit('Unexpected development state')
    dirs=sorted(p.name for p in (ROOT/'apps').iterdir() if p.is_dir())
    if dirs!=sorted(ACTIVE): raise SystemExit(f'Unexpected app roots: {dirs}')
    home=(ROOT/'index.html').read_text(encoding='utf-8')
    for app in ACTIVE:
        if f'./apps/{app}/index.html' not in home: raise SystemExit(f'Home route missing: {app}')
        idx=ROOT/f'apps/{app}/index.html'; text=idx.read_text(encoding='utf-8')
        if '../../index.html' not in text or 'aria-label="Home"' not in text: raise SystemExit(f'Home bridge missing: {app}')
        entry=lock['apps'][app]
        if sha(idx)!=entry['integratedIndexSha256']: raise SystemExit(f'Integrated index hash changed: {app}')
        if tree_digest(ROOT/f'apps/{app}',exclude=('index.html',))!=entry['nonIndexTreeSha256']: raise SystemExit(f'Frozen non-index source changed: {app}')
    if 'PDF Workspace' not in home or 'Coming soon' in home: raise SystemExit('PDF route must be active')
    starts={'documents':('startNew','startOpen'),'spreadsheets':('startNew','startOpen'),'presentations':('startNew','startOpen'),'txt':('startNew','startOpen'),'epub':('openStartBtn',),'pdf':('openStartBtn',)}
    for app,ids in starts.items():
        text=(ROOT/f'apps/{app}/index.html').read_text(encoding='utf-8')
        if 'start-card' not in text: raise SystemExit(f'Standard start card missing: {app}')
        for ident in ids:
            if f'id=\"{ident}\"' not in text: raise SystemExit(f'Start action {ident} missing: {app}')
    presentation=(ROOT/'apps/presentations/index.html').read_text(encoding='utf-8')
    for marker in ('presentationStartGate','showStart()','waitForOpenCommit','app.newPresentation()'):
        if marker not in presentation: raise SystemExit(f'Presentations startup gate missing: {marker}')
    if 'display:grid!important' not in presentation or '.start-state[hidden]{display:none!important}' not in presentation:
        raise SystemExit('Presentations startup gate visibility contract missing')
    if './apps/presentations/index.html?v=2.0.2' not in home:
        raise SystemExit('Versioned Home route for Presentations is missing')
    pdf=(ROOT/'apps/pdf/index.html').read_text()
    for marker in ('pdfStartGate','new MutationObserver(syncStart)','syncStart()'):
        if marker not in pdf: raise SystemExit('PDF start gate missing: '+marker)
    if list((ROOT/'apps/pdf').rglob('*.pdf')) or (ROOT/'apps/pdf/tests').exists(): raise SystemExit('PDF distribution contains internal fixtures')
    forbidden=('suite-shell.js','file-router.js','recent-files.js','module-loader.js','shared/app-shell.js')
    for marker in forbidden:
        if marker in home: raise SystemExit(f'Legacy Home runtime reference: {marker}')
    print('Repository structure and frozen-app locks validated.')
if __name__=='__main__': main()
