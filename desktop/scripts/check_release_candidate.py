#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

SEMVER=re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$')
APPS=('documents','spreadsheets','presentations','pdf','txt','epub')

def fail(msg:str)->None: raise SystemExit(msg)
def read(root:Path, rel:str)->str: return (root/rel).read_text(encoding='utf-8')

def check(root:Path, expected:str)->None:
    if not SEMVER.fullmatch(expected): fail(f'invalid expected semantic version: {expected!r}')
    meta=json.loads(read(root,'VERSION.json'))
    if meta.get('version')!=expected: fail(f'VERSION.json mismatch: {meta.get("version")!r} != {expected!r}')
    if meta.get('releaseName')!=f'InkDOS {expected}': fail('VERSION.json releaseName mismatch')
    tauri=json.loads(read(root,'desktop/src-tauri/tauri.conf.json'))
    if str(tauri.get('version','')).strip()!=expected: fail('tauri.conf.json version mismatch')
    cargo=read(root,'desktop/src-tauri/Cargo.toml').split('[package]',1)[1].split('[build-dependencies]',1)[0]
    m=re.search(r'^version\s*=\s*"([^"]+)"',cargo,re.M)
    if not m or m.group(1)!=expected: fail('Cargo.toml package version mismatch')
    home=read(root,'index.html')
    if f'./assets/home.css?v={expected}' not in home: fail('Home stylesheet cache-buster mismatch')
    for app in APPS:
        if f'./apps/{app}/index.html?v={expected}&amp;suite=1' not in home:
            fail(f'Home route cache-buster mismatch: {app}')
    sw=read(root,'service-worker.js')
    if not re.search(rf"const CACHE_NAME=['\"]inkdos-v{re.escape(expected)}-[^'\"]+['\"]",sw):
        fail('service-worker cache version mismatch')
    print(f'InkDOS release candidate version surfaces are consistent: {expected}')

def main()->int:
    p=argparse.ArgumentParser(description='Fail closed unless all final-version surfaces match the requested InkDOS release candidate.')
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--version',required=True)
    a=p.parse_args(); check(a.root.resolve(),a.version); return 0
if __name__=='__main__': raise SystemExit(main())
