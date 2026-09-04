#!/usr/bin/env python3
"""Reject retired runtime/branding layers from the active InkDOS tree."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = (
    'native-pdf-object',
    'native-pdf-embed',
    'native-mount',
    'native-status',
    'pdf.min.mjs',
    'pdf.worker.min.mjs',
    ('ink' + 'desk').lower(),
    ('visual-foundation-v' + '0203.css').lower(),
    ('content-workspaces-v' + '02031.css').lower(),
    ('workspace-unification-v' + '02031.css').lower(),
    ('spreadsheets-' + 'beta1-polish.css').lower(),
    ('light-' + 'only.css').lower(),
)
SKIP_PARTS = {'.git', '__pycache__', 'test-results', 'vendor', 'fixtures', 'compatibility-fixtures'}
TEXT_EXTENSIONS = {'.html', '.css', '.js', '.json', '.md', '.py', '.yml', '.yaml', '.cff', '.webmanifest'}
errors = []
for path in ROOT.rglob('*'):
    if not path.is_file() or path.name == 'check_no_legacy_runtime.py':
        continue
    rel = path.relative_to(ROOT)
    if any(part in SKIP_PARTS for part in rel.parts):
        continue
    if rel.parts[:2] == ('.github', 'workflows'):
        continue
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        continue
    text = path.read_text(encoding='utf-8', errors='ignore').lower()
    for token in TOKENS:
        if token in text:
            errors.append(f'{rel}: {token}')
if errors:
    print('Retired InkDOS tokens found:')
    for error in errors:
        print('-', error)
    raise SystemExit(1)
print('Active InkDOS tree contains no retired branding/runtime tokens.')
