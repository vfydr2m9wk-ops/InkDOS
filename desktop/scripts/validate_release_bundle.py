#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import unquote,urlparse
PLATFORMS={'windows-x86_64':('.exe','.exe.sig'),'darwin-aarch64':('.app.tar.gz','.app.tar.gz.sig'),'linux-x86_64':('.AppImage','.AppImage.sig')}
def fail(msg): raise SystemExit(msg)
def one(root,suffix):
 m=sorted(p for p in root.iterdir() if p.is_file() and p.name.endswith(suffix));
 if len(m)!=1: fail(f'Expected exactly one *{suffix}, found {len(m)}')
 return m[0]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--version',required=True); ap.add_argument('--tag',required=True); ap.add_argument('--assets',default='release-final'); a=ap.parse_args()
 if a.tag!=f'v{a.version}': fail('Release tag/version mismatch')
 root=Path(a.assets); manifest_path=root/'latest.json'; sums_path=root/'SHA256SUMS'
 if not manifest_path.is_file() or not sums_path.is_file(): fail('latest.json and SHA256SUMS are required')
 manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
 if manifest.get('version')!=a.version: fail('Updater manifest version mismatch')
 lines=sums_path.read_text(encoding='utf-8').splitlines(); sums={}
 for line in lines:
  m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
  if not m or m.group(2) in sums: fail('Malformed or duplicate SHA256SUMS entry')
  sums[m.group(2)]=m.group(1)
 inventory=[p for p in root.iterdir() if p.is_file() and p.name not in {'latest.json','SHA256SUMS'}]
 if set(sums)!=set(p.name for p in inventory): fail('SHA256SUMS inventory mismatch')
 for p in inventory:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=sums[p.name]: fail(f'Stale SHA256SUMS entry: {p.name}')
 platforms=manifest.get('platforms');
 if not isinstance(platforms,dict) or set(platforms)!=set(PLATFORMS): fail('Updater manifest platform set mismatch')
 for platform,(artifact_suffix,sig_suffix) in PLATFORMS.items():
  artifact=one(root,artifact_suffix); sig=one(root,sig_suffix); entry=platforms[platform]
  expected_path=f'/vfydr2m9wk-ops/InkDOS/releases/download/{a.tag}/{artifact.name}'
  u=urlparse(entry.get('url',''))
  if u.scheme!='https' or u.netloc!='github.com' or unquote(u.path)!=expected_path: fail(f'Updater URL mismatch: {platform}')
  if entry.get('signature')!=sig.read_text(encoding='utf-8').strip(): fail(f'Updater signature mismatch: {platform}')
 print('Release bundle coherence validated.')
 return 0
if __name__=='__main__': raise SystemExit(main())
