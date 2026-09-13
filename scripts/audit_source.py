#!/usr/bin/env python3
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
TEXT={'.html','.css','.js','.json','.md','.py','.txt','.yml','.yaml','.webmanifest'}
remote_script=re.compile(r'<script[^>]+src=["\']https?://',re.I)
remote_fetch=re.compile(r'\b(?:fetch|importScripts)\s*\(\s*["\']https?://',re.I)
local_path=re.compile(r'(?:file:///var/mobile/|/var/mobile/Containers/|/mnt/data/|/home/oai/)',re.I)
email=re.compile(r'(?<![\w.-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])',re.I)
def main():
    errors=[]; emails=[]
    for p in ROOT.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in TEXT: continue
        rel=p.relative_to(ROOT).as_posix()
        if '.github/workflows/' in rel or rel=='scripts/audit_source.py': continue
        text=p.read_text(encoding='utf-8',errors='ignore')
        if remote_script.search(text) or remote_fetch.search(text): errors.append(f'remote executable runtime: {rel}')
        if local_path.search(text): errors.append(f'local/container path: {rel}')
        # Ignore CODEOWNERS-style GitHub usernames; only flag actual email shapes outside license text.
        if not rel.startswith('licenses/'):
            for m in email.findall(text): emails.append((rel,m))
    if emails: errors.extend(f'email-shaped value: {rel}' for rel,_ in emails)
    if errors: raise SystemExit('\n'.join(errors))
    print('Source/privacy audit passed.')
if __name__=='__main__': main()
