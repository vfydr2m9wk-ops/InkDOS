#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib
from pathlib import Path

REQUIRED = ('.exe', '.dmg', '.AppImage', '.exe.sig', '.app.tar.gz', '.app.tar.gz.sig', '.AppImage.sig')
VERSIONED = ('.exe', '.AppImage')
PAIRS = (('.exe', '.exe.sig'), ('.AppImage', '.AppImage.sig'), ('.app.tar.gz', '.app.tar.gz.sig'))

def one(root: Path, suffix: str) -> Path:
    matches=sorted(p for p in root.iterdir() if p.is_file() and p.name.endswith(suffix) and (suffix.endswith('.sig') or not p.name.endswith('.sig')))
    if len(matches)!=1:
        raise SystemExit(f'Expected exactly one *{suffix} release asset, found {len(matches)}: '+(', '.join(p.name for p in matches) or 'none'))
    return matches[0]

def main()->int:
    ap=argparse.ArgumentParser(description='Fail-closed validation and SHA-256 inventory for selected InkDOS release artifacts.')
    ap.add_argument('--version',required=True); ap.add_argument('--assets',default='release-final'); ap.add_argument('--output',default='release-final/SHA256SUMS')
    a=ap.parse_args(); root=Path(a.assets)
    if not root.is_dir(): raise SystemExit(f'Release asset directory does not exist: {root}')
    chosen={s:one(root,s) for s in REQUIRED}
    prefix=f'InkDOS_{a.version}_'
    for suffix in VERSIONED:
        if not chosen[suffix].name.startswith(prefix):
            raise SystemExit(f'Release artifact/version mismatch: artifact={chosen[suffix].name!r}, version={a.version!r}')
    for artifact_suffix,sig_suffix in PAIRS:
        artifact=chosen[artifact_suffix]; sig=chosen[sig_suffix]
        if sig.name != artifact.name+'.sig':
            raise SystemExit(f'Release artifact/signature mismatch: artifact={artifact.name!r}, signature={sig.name!r}')
        if not sig.read_text(encoding='utf-8').strip(): raise SystemExit(f'Release signature is empty: {sig.name}')
    artifacts=sorted(set(chosen.values()),key=lambda p:p.name)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    lines=[f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}' for p in artifacts]
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Validated {len(artifacts)} release artifacts; wrote {out.as_posix()}')
    return 0
if __name__=='__main__': raise SystemExit(main())
