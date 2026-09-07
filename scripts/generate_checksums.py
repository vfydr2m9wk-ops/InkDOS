#!/usr/bin/env python3
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'CHECKSUMS.sha256'}
def ignored(p):
    rel=p.relative_to(ROOT)
    return p.name in EXCLUDE or '.git' in rel.parts or '__pycache__' in rel.parts or (rel.parts[:2]==('.github','workflows')) or (p.name.startswith('InkDOS-update-v') and p.suffix=='.zip')
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def main():
    rows=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and not ignored(p): rows.append(f"{digest(p)}  {p.relative_to(ROOT).as_posix()}")
    (ROOT/'CHECKSUMS.sha256').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    print(f'Generated {len(rows)} checksums.')
if __name__=='__main__': main()
