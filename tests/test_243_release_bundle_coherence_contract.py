#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SCRIPT=ROOT/'desktop/scripts/validate_release_bundle.py'
def run(*a): return subprocess.run([sys.executable,str(SCRIPT),*a],cwd=ROOT,text=True,capture_output=True)
def main():
  with tempfile.TemporaryDirectory() as td:
    d=Path(td); assets=d/'release-final'; assets.mkdir()
    files={'InkDOS_2.4.3_x64-setup.exe':b'win','InkDOS_2.4.3_x64-setup.exe.sig':b'wsig\n'}
    for n,b in files.items():(assets/n).write_bytes(b)
    (assets/'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(b).hexdigest()}  {n}\n' for n,b in sorted(files.items())),encoding='utf-8')
    manifest={'version':'2.4.3','notes':'','platforms':{
      'windows-x86_64':{'url':'https://github.com/vfydr2m9wk-ops/InkDOS/releases/download/v2.4.3/InkDOS_2.4.3_x64-setup.exe','signature':'wsig'}}}
    (assets/'latest.json').write_text(json.dumps(manifest),encoding='utf-8')
    ok=run('--version','2.4.3','--tag','v2.4.3','--assets',str(assets)); assert ok.returncode==0,(ok.stdout,ok.stderr)
    # stale checksum must fail closed
    sums=assets/'SHA256SUMS'; original=sums.read_text(); sums.write_text(original.replace(hashlib.sha256(b'win').hexdigest(),'0'*64),encoding='utf-8')
    bad=run('--version','2.4.3','--tag','v2.4.3','--assets',str(assets)); assert bad.returncode!=0
    sums.write_text(original,encoding='utf-8')
    # manifest signature must be the exact sidecar content
    m=json.loads((assets/'latest.json').read_text()); m['platforms']['windows-x86_64']['signature']='wrong'; (assets/'latest.json').write_text(json.dumps(m))
    bad=run('--version','2.4.3','--tag','v2.4.3','--assets',str(assets)); assert bad.returncode!=0
  print('InkDOS 2.4.3 release bundle coherence contract passed.')
if __name__=='__main__': main()
