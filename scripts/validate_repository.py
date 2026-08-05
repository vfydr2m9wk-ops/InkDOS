#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import shutil
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {'.git', 'dist', '__pycache__', '.DS_Store'}
errors: list[str] = []


def err(message: str) -> None:
    errors.append(message)


def files():
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        yield path, rel.as_posix()


required = [
    'index.html', 'VERSION.json', 'package.json', 'app-manifest.json',
    'service-worker.js', 'PDF.html', 'apps/pdf/index.html',
    'apps/pdf/app.js', 'apps/pdf/styles.css',
    'tests/fixtures/inkdesk-letterhead-a4.docx',
    'tests/fixtures/inkdesk-prescription-a4.xls',
    'tests/fixtures/inkdesk-prescription-a4.xlsx',
    'tests/fixtures/inkdesk-presentation-layout.pptx',
    'tests/fixtures/inkdesk-pdf-sample.pdf',
    'tests/fixtures/inkdesk-pdf-long-4000-pages.pdf',
]
for rel in required:
    if not (ROOT / rel).is_file():
        err('Missing required file: ' + rel)

try:
    version = json.loads((ROOT / 'VERSION.json').read_text())['version']
    for rel, key in [('package.json', 'version'), ('app-manifest.json', 'version')]:
        value = json.loads((ROOT / rel).read_text())[key]
        if value != version:
            err(f'{rel} version {value!r} != {version!r}')
    if version not in (ROOT / 'service-worker.js').read_text():
        err('Service-worker cache key does not contain the current version')
except Exception as exc:
    version = 'unknown'
    err('Version metadata unreadable: ' + str(exc))

for path, rel in files():
    if path.suffix.lower() == '.json' or path.name.endswith('.webmanifest'):
        try:
            json.loads(path.read_text())
        except Exception as exc:
            err(f'Invalid JSON: {rel}: {exc}')

ref_re = re.compile(r'''(?:href|src)=["']([^"']+)["']''', re.I)
for html, rel in [(p, r) for p, r in files() if p.suffix.lower() == '.html']:
    text = html.read_text(errors='replace')
    for raw in ref_re.findall(text):
        if raw.startswith(('http:', 'https:', 'data:', 'blob:', 'mailto:', 'javascript:', '#')):
            continue
        path = urlsplit(raw).path
        if not path:
            continue
        target = (html.parent / path).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            err(f'Path escapes repository: {rel} -> {raw}')
            continue
        if not target.exists():
            err(f'Broken local reference: {rel} -> {raw}')

try:
    manifest = json.loads((ROOT / 'app-manifest.json').read_text())
    for item in manifest.get('launchers', []):
        for key in ('entryPoint', 'icon'):
            rel = item.get(key, '')
            if not rel or not (ROOT / rel).is_file():
                err(f'Broken launcher {item.get("id")}: {key}={rel!r}')
except Exception as exc:
    err('app-manifest.json invalid: ' + str(exc))

service_worker = (ROOT / 'service-worker.js').read_text(errors='replace')
for rel in re.findall(r"'\./([^']+)'", service_worker.split('];', 1)[0]):
    if rel and rel != '/' and not (ROOT / rel).exists():
        err('Service-worker asset missing: ' + rel)
for rel in ('apps/pdf/index.html', 'apps/pdf/styles.css', 'apps/pdf/app.js', 'assets/icons/pdf.png'):
    if f"'./{rel}'" not in service_worker:
        err('PDF asset missing from service-worker shell: ' + rel)

by_hash: dict[str, list[str]] = {}
for path, rel in files():
    if path.stat().st_size == 0:
        if rel != '.nojekyll':
            err('Empty file: ' + rel)
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    by_hash.setdefault(digest, []).append(rel)
for group in by_hash.values():
    if len(group) > 1:
        err('Exact duplicate files: ' + ', '.join(group))

for pattern in ('*0.18.5*', '*0.19.2-beta*', '*validation-contact-sheet*'):
    for path in ROOT.rglob(pattern):
        if not any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts):
            err('Stale file remains: ' + path.relative_to(ROOT).as_posix())

# Syntax-check project JavaScript. Vendor bundles are trusted third-party files and are skipped.
node = shutil.which('node')
if node:
    for path, rel in files():
        if path.suffix.lower() != '.js' or rel.startswith('shared/vendor/'):
            continue
        result = subprocess.run([node, '--check', str(path)], capture_output=True, text=True)
        if result.returncode:
            err(f'JavaScript syntax error: {rel}: {result.stderr.strip()}')

# Verify generated source and runtime manifests entry-by-entry.
source_path = ROOT / 'SOURCE_MANIFEST.json'
if source_path.is_file():
    try:
        source = json.loads(source_path.read_text())
        for item in source.get('files', []):
            rel = item['path']
            path = ROOT / rel
            if not path.is_file():
                err('SOURCE_MANIFEST missing path: ' + rel)
                continue
            if path.stat().st_size != item['bytes']:
                err('SOURCE_MANIFEST size mismatch: ' + rel)
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                err('SOURCE_MANIFEST hash mismatch: ' + rel)
    except Exception as exc:
        err('SOURCE_MANIFEST invalid: ' + str(exc))

checksums = ROOT / 'RUNTIME_CHECKSUMS.sha256'
if checksums.is_file():
    for line_number, line in enumerate(checksums.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            digest, rel = line.split('  ', 1)
        except ValueError:
            err(f'RUNTIME_CHECKSUMS malformed line {line_number}')
            continue
        path = ROOT / rel
        if not path.is_file():
            err('RUNTIME_CHECKSUMS missing path: ' + rel)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            err('RUNTIME_CHECKSUMS hash mismatch: ' + rel)

if errors:
    print('\n'.join('ERROR: ' + message for message in errors))
    sys.exit(1)

count = sum(1 for _ in files())
print(f'OK: repository structure valid ({count} distributable files, version {version}).')
