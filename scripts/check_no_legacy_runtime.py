#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = (
    'native-pdf-object',
    'native-pdf-embed',
    'native-mount',
    'native-status',
    'pdf.min.mjs',
    'pdf.worker.min.mjs',
)
errors = []
for path in ROOT.rglob('*'):
    if not path.is_file() or any(
        part in {'.git', '__pycache__', 'test-results'}
        for part in path.parts
    ):
        continue
    if path.suffix.lower() not in {
        '.html', '.css', '.js', '.json', '.md', '.py', '.yml', '.yaml'
    }:
        continue
    text = path.read_text(encoding='utf-8', errors='ignore').lower()
    for token in TOKENS:
        if token in text and path.name != 'check_no_legacy_runtime.py':
            errors.append(f'{path.relative_to(ROOT)}: {token}')
if errors:
    print('Retired runtime tokens found:')
    for error in errors:
        print('-', error)
    raise SystemExit(1)
print('No retired PDF runtime tokens found.')
