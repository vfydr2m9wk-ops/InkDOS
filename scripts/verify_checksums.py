#!/usr/bin/env python3
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def main():
    f=ROOT/'CHECKSUMS.sha256'
    if not f.is_file(): raise SystemExit('CHECKSUMS.sha256 is missing')
    n=0
    for line in f.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        expected,rel=line.split('  ',1); p=ROOT/rel
        if not p.is_file(): raise SystemExit(f'Checksum target missing: {rel}')
        if digest(p)!=expected: raise SystemExit(f'Checksum mismatch: {rel}')
        n+=1
    print(f'Checksums verified: {n}.')
if __name__=='__main__': main()
