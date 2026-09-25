#!/usr/bin/env python3
"""Bind the offline shell and worker runtime to one verified byte snapshot."""
from pathlib import Path
import argparse
import hashlib
import json
import re
ROOT=Path(__file__).resolve().parents[1]
SHELL=re.compile(r'const APP_SHELL=(\[.*?\]);',re.S)
HASHES=re.compile(r'// BEGIN OFFLINE HASHES\n.*?// END OFFLINE HASHES\n',re.S)
CACHE=re.compile(r"const CACHE_NAME=['\"][^'\"]+['\"];\n")
def render(root: Path, source: str) -> str:
    paths=json.loads(SHELL.search(source)[1])
    if len(paths)!=len(set(paths)):raise ValueError('Duplicate offline shell path')
    hashes={}
    for rel in paths:
        p=(root/rel).resolve()
        if not rel.startswith('./') or not p.is_relative_to(root.resolve()) or not p.is_file():raise ValueError(f'Invalid offline shell path: {rel}')
        hashes[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    version=json.loads((root/'VERSION.json').read_text())['version']
    clean=HASHES.sub('',CACHE.sub('',source))
    digest=hashlib.sha256((clean+json.dumps(hashes,sort_keys=True)).encode()).hexdigest()[:20]
    block='// BEGIN OFFLINE HASHES\nconst ASSET_HASHES='+json.dumps(hashes,indent=2,sort_keys=True)+';\n// END OFFLINE HASHES\n'
    header=f"const CACHE_NAME='inkdos-v{version}-{digest}';\n"
    return clean.replace("'use strict';\n","'use strict';\n"+header+block,1)
def build(root: Path=ROOT,check: bool=False) -> None:
    path=root/'service-worker.js';source=path.read_text();expected=render(root,source)
    if check:
        if source!=expected:
            first=next((i for i,(a,b) in enumerate(zip(source,expected)) if a!=b),min(len(source),len(expected)))
            print('OFFLINE_SNAPSHOT_FIRST_DIFF',first)
            print('SOURCE_SLICE',repr(source[max(0,first-120):first+240]))
            print('EXPECTED_SLICE',repr(expected[max(0,first-120):first+240]))
            source_hashes=json.loads(re.search(r'const ASSET_HASHES=(\{.*?\});',source,re.S)[1])
            expected_hashes=json.loads(re.search(r'const ASSET_HASHES=(\{.*?\});',expected,re.S)[1])
            diffs={k:{'source':source_hashes.get(k),'expected':expected_hashes.get(k)} for k in sorted(set(source_hashes)|set(expected_hashes)) if source_hashes.get(k)!=expected_hashes.get(k)}
            print('OFFLINE_HASH_DIFFS',json.dumps(diffs,sort_keys=True))
            print('EXPECTED_CACHE',CACHE.search(expected)[0].strip())
            raise SystemExit('Offline snapshot is stale; run python scripts/build_offline_snapshot.py')
        print('Offline snapshot matches current source bytes.')
    else:path.write_text(expected)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();build(a.root,a.check)
