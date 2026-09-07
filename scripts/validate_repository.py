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
    if v.get('version')!='2.0.12': raise SystemExit('Unexpected version')
    if state.get('appliedSequence')!=80 or state.get('currentPackage')!='2.0.12-modularity-epub-polish': raise SystemExit('Unexpected development state')
    dirs=sorted(p.name for p in (ROOT/'apps').iterdir() if p.is_dir())
    if dirs!=sorted(ACTIVE): raise SystemExit(f'Unexpected app roots: {dirs}')
    home=(ROOT/'index.html').read_text(encoding='utf-8')
    for app in ACTIVE:
        if f'./apps/{app}/index.html?v=2.0.12&amp;suite=1' not in home: raise SystemExit(f'Versioned suite Home route missing: {app}')
        idx=ROOT/f'apps/{app}/index.html'; text=idx.read_text(encoding='utf-8')
        if '../../index.html' not in text or 'aria-label="Home"' not in text: raise SystemExit(f'Optional Home anchor missing: {app}')
        entry=lock['apps'][app]
        if sha(idx)!=entry['integratedIndexSha256']: raise SystemExit(f'Integrated index hash changed: {app}')
        if tree_digest(ROOT/f'apps/{app}',exclude=('index.html',))!=entry['nonIndexTreeSha256']: raise SystemExit(f'Integrated non-index source changed: {app}')
    if 'PDF Workspace' not in home or 'Coming soon' in home: raise SystemExit('PDF route must be active')
    if (ROOT/'apps/pdf/assets/pdf.svg').read_bytes()!=(ROOT/'assets/icons/pdf.svg').read_bytes(): raise SystemExit('PDF app icon must match canonical Home icon')
    pdf_frame=(ROOT/'apps/pdf/runtime/frame/app-frame.css').read_text(encoding='utf-8')
    for marker in ('.document-title{position:absolute;left:50%', '.title-text{height:100%', 'border:1px solid var(--line)', '.pdf-icon{width:30px'):
        if marker not in pdf_frame: raise SystemExit('PDF frame title alignment missing: '+marker)
    if "inkdos2:appearance" not in home or 'id="appearanceButton"' not in home or 'id="appearanceMenu"' not in home: raise SystemExit('Home appearance control missing')
    home_css=(ROOT/'assets/home.css').read_text(encoding='utf-8')
    if 'html[data-theme="dark"]' not in home_css: raise SystemExit('Home dark appearance missing')
    local_keys={
        'documents':'inkdos2:documents:appearance','spreadsheets':'inkdos2:spreadsheets:appearance','presentations':'inkdos2:presentations:appearance',
        'txt':'inkdos2:txt:appearance','epub':'inkdos2:epub:appearance','pdf':'inkdos2:pdf:p1:appearance'}
    for app,local_key in local_keys.items():
        appearance=(ROOT/'apps'/app/'state'/'appearance.js').read_text(encoding='utf-8')
        if local_key not in appearance: raise SystemExit(f'App-local appearance key missing: {app}')
        if 'inkdos2:appearance' not in appearance or "'storage'" not in appearance: raise SystemExit(f'Horizontal appearance bridge missing: {app}')
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
    pdf=(ROOT/'apps/pdf/index.html').read_text()
    for marker in ('pdfStartGate','new MutationObserver(syncStart)','syncStart()'):
        if marker not in pdf: raise SystemExit('PDF start gate missing: '+marker)
    if list((ROOT/'apps/pdf').rglob('*.pdf')) or (ROOT/'apps/pdf/tests').exists(): raise SystemExit('PDF distribution contains internal fixtures')
    sw=(ROOT/'service-worker.js').read_text(encoding='utf-8')
    if "inkdos-v2.0.12-modularity-epub-polish-seq80" not in sw: raise SystemExit('2.0.12 offline cache rotation missing')
    forbidden=('suite-shell.js','file-router.js','recent-files.js','module-loader.js','shared/app-shell.js')
    for marker in forbidden:
        if marker in home: raise SystemExit(f'Legacy Home runtime reference: {marker}')
    print('Repository structure and integrated-app locks validated.')
if __name__=='__main__': main()
