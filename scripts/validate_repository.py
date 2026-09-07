#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
ACTIVE=('documents','spreadsheets','presentations','txt','epub')
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
    if v.get('version')!='2.0.0': raise SystemExit('Unexpected version')
    if state.get('appliedSequence')!=68 or state.get('currentPackage')!='2.0.0-clean-snapshot': raise SystemExit('Unexpected development state')
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
    if (ROOT/'apps/pdf').exists(): raise SystemExit('PDF runtime must not exist in 2.0.0')
    if 'PDF Workspace' not in home or 'Coming soon' not in home: raise SystemExit('PDF placeholder missing')
    forbidden=('suite-shell.js','file-router.js','recent-files.js','module-loader.js','shared/app-shell.js')
    for marker in forbidden:
        if marker in home: raise SystemExit(f'Legacy Home runtime reference: {marker}')
    print('Repository structure and frozen-app locks validated.')
if __name__=='__main__': main()
