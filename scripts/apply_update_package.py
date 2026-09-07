#!/usr/bin/env python3
"""Transactional InkDOS updater. Full-snapshot mode builds the candidate from package bytes only."""
from __future__ import annotations
from pathlib import Path, PurePosixPath
import argparse,hashlib,json,shutil,subprocess,sys,tempfile,zipfile
PRODUCT='InkDOS'; WORKFLOWS='.github/workflows/'; STATE='DEVELOPMENT_STATE.json'; VERSION='VERSION.json'
MAX_ENTRIES=10000; MAX_SINGLE=128*1024*1024; MAX_TOTAL=512*1024*1024
class UpdateError(RuntimeError): pass
def load(p):
    try:return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception as e: raise UpdateError(f'Invalid JSON {p}: {e}') from e
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def safe(raw):
    if not isinstance(raw,str) or not raw or '\\' in raw: raise UpdateError(f'Unsafe path: {raw!r}')
    p=PurePosixPath(raw)
    if p.is_absolute() or any(x in ('','.','..') for x in p.parts): raise UpdateError(f'Unsafe path: {raw!r}')
    s=p.as_posix()
    if s=='.git' or s.startswith('.git/'): raise UpdateError('Git metadata is protected')
    if s=='.github/workflows' or s.startswith(WORKFLOWS): raise UpdateError('Workflow paths are protected')
    return p
def inspect(package):
    total=0; seen=set()
    with zipfile.ZipFile(package) as z:
        infos=z.infolist(); names={x.filename for x in infos}
        if len(infos)>MAX_ENTRIES: raise UpdateError('Too many ZIP entries')
        if 'patch-manifest.json' not in names or 'files/scripts/apply_update_package.py' not in names: raise UpdateError('Required update package files are missing')
        for info in infos:
            raw=info.filename.rstrip('/')
            if not raw: continue
            safe(raw); key=raw.casefold()
            if key in seen: raise UpdateError(f'Duplicate/case-colliding path: {raw}')
            seen.add(key); total+=info.file_size
            if info.file_size>MAX_SINGLE or total>MAX_TOTAL: raise UpdateError('ZIP size limit exceeded')
            if ((info.external_attr>>16)&0o170000)==0o120000: raise UpdateError('Symlinks are forbidden')
def extract(package,dest):
    with zipfile.ZipFile(package) as z:
        for info in z.infolist():
            if info.is_dir(): continue
            raw=info.filename; safe(raw)
            p=dest.joinpath(*PurePosixPath(raw).parts); p.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as src,p.open('wb') as dst: shutil.copyfileobj(src,dst)
def verify_payload(extracted,manifest):
    declared=manifest.get('files') or {}; payload=extracted/'files'
    actual={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
    if actual!=set(declared):
        missing=sorted(set(declared)-actual); extra=sorted(actual-set(declared)); raise UpdateError(f'Payload file-set mismatch; missing={missing[:5]} extra={extra[:5]}')
    for rel,meta in declared.items():
        safe(rel); got=sha(payload/rel)
        if got!=meta.get('sha256'): raise UpdateError(f'Payload SHA-256 mismatch: {rel}')
def validate_base(repo,m):
    state=load(repo/STATE); version=load(repo/VERSION); req=m.get('requires',{})
    if state.get('appliedSequence')!=req.get('previousSequence'): raise UpdateError(f"Base sequence mismatch: {state.get('appliedSequence')}")
    if m.get('sequence')!=state.get('appliedSequence',0)+1: raise UpdateError('Package sequence is not next')
    allowed=req.get('appVersions') or []
    if allowed and version.get('version') not in allowed: raise UpdateError(f"Base version not allowed: {version.get('version')}")
def copy_workflows(repo,candidate):
    src=repo/'.github/workflows'
    if not src.is_dir(): raise UpdateError('Protected update workflow directory is missing')
    shutil.copytree(src,candidate/'.github/workflows')
def overlay(payload,candidate):
    for src in sorted(payload.rglob('*')):
        if not src.is_file():continue
        rel=src.relative_to(payload).as_posix(); safe(rel); dst=candidate/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def write_state(candidate,m):
    (candidate/STATE).write_text(json.dumps({'schemaVersion':2,'appliedSequence':m['sequence'],'currentPackage':m['packageLabel'],'status':'complete'},indent=2)+'\n',encoding='utf-8')
def ignore_copy(directory,names): return {n for n in names if n in {'.git','__pycache__','.venv','node_modules','test-results'} or (n.startswith('InkDOS-update-v') and n.endswith('.zip'))}
def build(repo,extracted,candidate,m):
    mode=m.get('mode','incremental'); payload=extracted/'files'
    if mode=='full-snapshot':
        copy_workflows(repo,candidate); overlay(payload,candidate)
    elif mode=='incremental':
        shutil.copytree(repo,candidate,dirs_exist_ok=True,ignore=ignore_copy); overlay(payload,candidate)
        delete=extracted/'DELETE.txt'
        if delete.is_file():
            for line in delete.read_text(encoding='utf-8').splitlines():
                raw=line.strip()
                if not raw or raw.startswith('#'):continue
                rel=safe(raw); p=candidate.joinpath(*rel.parts)
                if p.is_dir():shutil.rmtree(p)
                elif p.exists():p.unlink()
    else: raise UpdateError(f'Unsupported update mode: {mode}')
    write_state(candidate,m)
def fmap(root):
    root=Path(root); out={}
    for p in root.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(root).as_posix()
        if rel.startswith('.git/') or '__pycache__/' in rel or rel.startswith('.venv/') or rel.startswith('node_modules/') or (p.name.startswith('InkDOS-update-v') and p.suffix=='.zip'):continue
        out[rel]=sha(p)
    return out
def ensure_workflow_identity(repo,candidate):
    def only(m):return {k:v for k,v in m.items() if k.startswith(WORKFLOWS)}
    if only(fmap(repo))!=only(fmap(candidate)): raise UpdateError('Candidate changed protected workflows')
def run_validation(candidate,profile):
    if profile=='none':return
    py=sys.executable
    cmd=[py,'scripts/run_release_validation.py'] if profile=='full' else [py,'scripts/validate_repository.py']
    subprocess.run(cmd,cwd=candidate,check=True)
def apply_diff(repo,candidate):
    before=fmap(repo); after=fmap(candidate)
    changed=sorted(k for k,v in after.items() if before.get(k)!=v); deleted=sorted(k for k in before if k not in after)
    for rel in changed+deleted:
        if rel.startswith(WORKFLOWS): raise UpdateError('Workflow mutation refused')
    touched=sorted(set(changed+deleted))
    with tempfile.TemporaryDirectory(prefix='inkdos-rollback-') as td:
        backup=Path(td); snapshots={}
        try:
            for rel in touched:
                p=repo/rel
                if p.is_file():
                    b=backup/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,b);snapshots[rel]=b
                else:snapshots[rel]=None
            for rel in deleted:
                p=repo/rel
                if p.is_file():p.unlink()
                elif p.is_dir():shutil.rmtree(p)
            for rel in changed:
                src=candidate/rel;dst=repo/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
            # Remove empty directories left behind by the deleted 1.x tree. Git would
            # discard them on the next checkout, but full-snapshot mode also cleans
            # the live transaction workspace immediately.
            dirs=sorted((p for p in repo.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True)
            for d in dirs:
                rel=d.relative_to(repo).as_posix()
                if rel=='.git' or rel.startswith('.git/') or rel=='.github' or rel=='.github/workflows' or rel.startswith('.github/workflows/'):
                    continue
                try:d.rmdir()
                except OSError:pass
        except Exception:
            for rel in touched:
                p=repo/rel
                if p.is_file():p.unlink()
                elif p.is_dir():shutil.rmtree(p)
                snap=snapshots[rel]
                if snap is not None:
                    p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(snap,p)
            raise
    return [x for x in changed if x not in before],[x for x in changed if x in before],deleted
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--package',required=True);ap.add_argument('--repo',required=True);ap.add_argument('--report',required=True);ap.add_argument('--dry-run',action='store_true');ap.add_argument('--validation-profile',choices=['none','standard','full']);a=ap.parse_args()
    package=Path(a.package).resolve();repo=Path(a.repo).resolve();report=Path(a.report);result={'status':'failed'}
    try:
        inspect(package)
        with tempfile.TemporaryDirectory(prefix='inkdos-extract-') as exn,tempfile.TemporaryDirectory(prefix='inkdos-candidate-') as can:
            ex=Path(exn);candidate=Path(can);extract(package,ex);m=load(ex/'patch-manifest.json')
            if m.get('product')!=PRODUCT:raise UpdateError('Wrong product')
            if m.get('allowWorkflowChanges'):raise UpdateError('Workflow changes are forbidden')
            validate_base(repo,m);verify_payload(ex,m);build(repo,ex,candidate,m);ensure_workflow_identity(repo,candidate)
            profile=a.validation_profile or m.get('validationProfile','full');run_validation(candidate,profile)
            if a.dry_run:added=replaced=deleted=[];status='validated'
            else:added,replaced,deleted=apply_diff(repo,candidate);status='applied'
            result.update({'status':status,'packageLabel':m['packageLabel'],'targetRelease':m.get('targetRelease'),'sequence':m['sequence'],'validationProfile':profile,'mode':m.get('mode'),'copied':added+replaced,'added':added,'replaced':replaced,'deleted':deleted})
    except Exception as e:
        result['error']=str(e);report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(f'Update failed: {e}',file=sys.stderr);raise
    report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
