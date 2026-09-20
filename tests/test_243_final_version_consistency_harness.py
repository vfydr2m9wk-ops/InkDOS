#!/usr/bin/env python3
from __future__ import annotations
import contextlib, importlib.util, io, json, re, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CHECK=ROOT/'desktop/scripts/check_release_candidate.py'
SPEC=importlib.util.spec_from_file_location('inkdos_check_release_candidate', CHECK)
assert SPEC and SPEC.loader
CHECKER=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(CHECKER)
FILES=('VERSION.json','desktop/src-tauri/tauri.conf.json','desktop/src-tauri/Cargo.toml','index.html','service-worker.js')

def run(root:Path,version=None):
    if version is None:
        version=json.loads((root/'VERSION.json').read_text(encoding='utf-8'))['version']
    output=io.StringIO()
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            CHECKER.check(root.resolve(),version)
    except SystemExit as exc:
        return 1, output.getvalue() + str(exc)
    return 0, output.getvalue()

def write(path:Path,text:str):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')

def stale_version(version:str)->str:
    major,minor,patch=(int(x) for x in version.split('.'))
    if patch>0:
        return f'{major}.{minor}.{patch-1}'
    if minor>0:
        return f'{major}.{minor-1}.0'
    return f'{max(0,major-1)}.0.0'

def main():
    meta=json.loads((ROOT/'VERSION.json').read_text(encoding='utf-8'))
    version=meta['version']
    stale=stale_version(version)
    ok=run(ROOT,version)
    assert ok[0]==0,ok[1]

    with tempfile.TemporaryDirectory() as td:
        t=Path(td)
        for rel in FILES:
            write(t/rel,(ROOT/rel).read_text(encoding='utf-8'))
        originals={rel:(t/rel).read_text(encoding='utf-8') for rel in FILES}
        mutations={
          'VERSION.json':lambda s:s.replace(f'"releaseName": "InkDOS {version}"',f'"releaseName": "InkDOS {stale}"',1),
          'desktop/src-tauri/tauri.conf.json':lambda s:s.replace(f'"version": "{version}"',f'"version": "{stale}"',1),
          'desktop/src-tauri/Cargo.toml':lambda s:re.sub(rf'(?m)^(version\s*=\s*"){re.escape(version)}("\s*)$',rf'\g<1>{stale}\2',s,count=1),
          'index.html':lambda s:s.replace(f'v={version}',f'v={stale}',1),
          'service-worker.js':lambda s:s.replace(f'inkdos-v{version}-',f'inkdos-v{stale}-',1),
        }
        for rel,mutate in mutations.items():
            changed=mutate(originals[rel])
            assert changed!=originals[rel],f'mutation did not change {rel}'
            write(t/rel,changed)
            bad=run(t,version)
            assert bad[0]!=0,(rel,bad[1])
            write(t/rel,originals[rel])

    print(f'InkDOS {version} final-version consistency harness contract passed.')

if __name__=='__main__':
    main()
