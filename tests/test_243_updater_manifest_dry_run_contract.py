#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'desktop/scripts/build_updater_manifest.py'

def run(*args):
    return subprocess.run([sys.executable,str(SCRIPT),*args],cwd=ROOT,text=True,capture_output=True)

def main():
    with tempfile.TemporaryDirectory() as td:
        t=Path(td); a=t/'assets'; a.mkdir()
        fixtures={
          'InkDOS_2.4.3_x64-setup.exe':b'win', 'InkDOS_2.4.3_x64-setup.exe.sig':b'WIN243SIG\n',
          'InkDOS.app.tar.gz':b'mac', 'InkDOS.app.tar.gz.sig':b'MAC243SIG\n',
          'InkDOS_2.4.3_amd64.AppImage':b'linux', 'InkDOS_2.4.3_amd64.AppImage.sig':b'LINUX243SIG\n'}
        for n,b in fixtures.items():(a/n).write_bytes(b)
        notes=t/'notes.md'; notes.write_text('InkDOS 2.4.3 dry-run notes.\n',encoding='utf-8')
        out=t/'latest.json'
        ok=run('--version','2.4.3','--tag','v2.4.3','--assets',str(a),'--notes',str(notes),'--output',str(out))
        assert ok.returncode==0,ok.stderr
        m=json.loads(out.read_text(encoding='utf-8'))
        assert m['version']=='2.4.3'
        expected={'windows-x86_64':('InkDOS_2.4.3_x64-setup.exe','WIN243SIG'),'darwin-aarch64':('InkDOS.app.tar.gz','MAC243SIG'),'linux-x86_64':('InkDOS_2.4.3_amd64.AppImage','LINUX243SIG')}
        for platform,(name,sig) in expected.items():
            e=m['platforms'][platform]
            assert e['url'].endswith('/releases/download/v2.4.3/'+name),(platform,e)
            assert e['signature']==sig,(platform,e)
        bad=run('--version','2.4.3','--tag','v2.4.2','--assets',str(a),'--notes',str(notes),'--output',str(t/'bad.json'))
        assert bad.returncode!=0,'manifest builder must reject a tag/version mismatch'
        assert not (t/'bad.json').exists(),'rejected manifest must not be written'
        # A correct tag must not be allowed to publish a stale versioned artifact.
        (a/'InkDOS_2.4.3_x64-setup.exe').rename(a/'InkDOS_2.4.2_x64-setup.exe')
        (a/'InkDOS_2.4.3_x64-setup.exe.sig').rename(a/'InkDOS_2.4.2_x64-setup.exe.sig')
        stale=t/'stale.json'
        stale_result=run('--version','2.4.3','--tag','v2.4.3','--assets',str(a),'--notes',str(notes),'--output',str(stale))
        assert stale_result.returncode!=0,'manifest builder must reject a stale Windows artifact version'
        assert not stale.exists(),'stale-artifact manifest must not be written'

        # The signature must belong to the selected artifact, not merely share its suffix.
        (a/'InkDOS_2.4.2_x64-setup.exe').rename(a/'InkDOS_2.4.3_x64-setup.exe')
        mismatched_sig=a/'Other_2.4.3_x64-setup.exe.sig'
        (a/'InkDOS_2.4.2_x64-setup.exe.sig').rename(mismatched_sig)
        mismatch=t/'mismatch.json'
        mismatch_result=run('--version','2.4.3','--tag','v2.4.3','--assets',str(a),'--notes',str(notes),'--output',str(mismatch))
        assert mismatch_result.returncode!=0,'manifest builder must reject a signature not paired by exact artifact basename'
        assert not mismatch.exists(),'mismatched-signature manifest must not be written'
    print('InkDOS 2.4.3 updater manifest dry-run contract passed.')
    return 0
if __name__=='__main__': raise SystemExit(main())
