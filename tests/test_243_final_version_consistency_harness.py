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

def run(root:Path,version='2.4.3'):
    # Exercise the real validator in-process: process startup dominates this matrix in
    # constrained Library runtimes and adds no isolation value because check() is pure.
    output=io.StringIO()
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            CHECKER.check(root.resolve(),version)
    except SystemExit as exc:
        return 1, output.getvalue() + str(exc)
    return 0, output.getvalue()
def write(path:Path,text:str): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')

def main():
    baseline=json.loads((ROOT/'VERSION.json').read_text(encoding='utf-8'))
    assert baseline['version']=='2.4.3', baseline
    ok=run(ROOT); assert ok[0]==0,ok[1]
    with tempfile.TemporaryDirectory() as td:
        t=Path(td)
        for rel in FILES: write(t/rel,(ROOT/rel).read_text(encoding='utf-8'))
        # Every independently stale surface must fail closed.
        originals={rel:(t/rel).read_text() for rel in FILES}
        mutations={
          'VERSION.json':lambda s:s.replace('"releaseName": "InkDOS 2.4.3"','"releaseName": "InkDOS 2.4.2"'),
          'desktop/src-tauri/tauri.conf.json':lambda s:s.replace('"version": "2.4.3"','"version": "2.4.2"',1),
          'desktop/src-tauri/Cargo.toml':lambda s:s.replace('version = "2.4.3"','version = "2.4.2"',1),
          'index.html':lambda s:s.replace('v=2.4.3','v=2.4.2',1),
          'service-worker.js':lambda s:s.replace('inkdos-v2.4.3-','inkdos-v2.4.2-',1),
        }
        for rel,mutate in mutations.items():
            write(t/rel,mutate(originals[rel])); bad=run(t); assert bad[0]!=0,(rel,bad[1]); write(t/rel,originals[rel])
    print('InkDOS 2.4.3 final-version consistency harness contract passed.')
if __name__=='__main__': main()
