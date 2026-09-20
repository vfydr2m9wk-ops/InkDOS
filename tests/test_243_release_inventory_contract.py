#!/usr/bin/env python3
from __future__ import annotations
import hashlib, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SCRIPT=ROOT/'desktop/scripts/validate_release_inventory.py'
def run(*a): return subprocess.run([sys.executable,str(SCRIPT),*a],cwd=ROOT,text=True,capture_output=True)
def main():
  with tempfile.TemporaryDirectory() as td:
    t=Path(td); a=t/'assets'; a.mkdir(); out=t/'SHA256SUMS'
    fixtures={'InkDOS_2.4.3_x64-setup.exe':b'win','InkDOS_2.4.3_x64-setup.exe.sig':b'wsig\n','InkDOS_2.4.3_aarch64.dmg':b'dmg','InkDOS.app.tar.gz':b'mac','InkDOS.app.tar.gz.sig':b'msig\n','InkDOS_2.4.3_amd64.AppImage':b'lin','InkDOS_2.4.3_amd64.AppImage.sig':b'lsig\n'}
    for n,b in fixtures.items():(a/n).write_bytes(b)
    ok=run('--version','2.4.3','--assets',str(a),'--output',str(out)); assert ok.returncode==0,ok.stderr
    lines=out.read_text().splitlines(); assert len(lines)==7,lines
    for n,b in fixtures.items(): assert f'{hashlib.sha256(b).hexdigest()}  {n}' in lines
    # stale versioned installer must fail closed without writing an inventory
    out.unlink(); (a/'InkDOS_2.4.3_x64-setup.exe').rename(a/'InkDOS_2.4.2_x64-setup.exe')
    bad=run('--version','2.4.3','--assets',str(a),'--output',str(out)); assert bad.returncode!=0; assert not out.exists()
    (a/'InkDOS_2.4.2_x64-setup.exe').rename(a/'InkDOS_2.4.3_x64-setup.exe')
    # unrelated signature must never be accepted for an artifact
    (a/'InkDOS_2.4.3_x64-setup.exe.sig').rename(a/'Other.exe.sig')
    bad=run('--version','2.4.3','--assets',str(a),'--output',str(out)); assert bad.returncode!=0; assert not out.exists()
  print('InkDOS 2.4.3 release artifact inventory contract passed.')
if __name__=='__main__': main()
