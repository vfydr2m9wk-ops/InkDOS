#!/usr/bin/env python3
"""The interface density is always the desktop density (owner, 2026-10-10): shared/ui-density.js keeps its API and
the data-ui-density attribute, with no Auto/Desktop/Smartphone choice and no mobile layout left anywhere."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / 'shared' / 'ui-density.js'
CSS = ROOT / 'shared' / 'ui-density.css'


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f'{label}: forbidden {needle!r}')


def main() -> None:
    js = JS.read_text(encoding='utf-8')
    css = CSS.read_text(encoding='utf-8')
    require(js, 'data-ui-density', 'Density attribute')
    require(js, "'desktop'", 'Desktop density')
    for gone in ("'mobile'", "'auto'", 'installControl', 'matchMedia', 'Smartphone'):
        forbid(js, gone, 'Removed density choice')
    for forbidden in ['fetch(', 'XMLHttpRequest', 'WebSocket', 'sendBeacon']:
        forbid(js, forbidden, 'Density module must stay local-only')
    # the module still registers a workspace's offline worker and loads the shared settings
    require(js, 'serviceWorker.register', 'Workspace offline registration')
    require(js, 'settings-strip.js', 'Workspace settings bootstrap')

    require(css, '[data-ui-density="desktop"]', 'Desktop density CSS')
    require(css, '--control:', 'Shared density tokens')
    forbid(css, 'density-control', 'Removed density control CSS')

    # no stylesheet anywhere keeps a mobile-density rule
    for path in [ROOT / 'index.html', *ROOT.glob('apps/*/index.html'), ROOT / 'apps/txt/page.template.html',
                 *ROOT.glob('apps/*/**/*.css'), *ROOT.glob('shared/**/*.css'), *ROOT.glob('assets/*.css')]:
        if '/vendor/' in path.as_posix():
            continue
        forbid(path.read_text(encoding='utf-8'), 'data-ui-density="mobile"', f'Mobile density rule in {path.relative_to(ROOT)}')

    entries = {
        ROOT / 'index.html': ('./shared/ui-density.css', './shared/ui-density.js'),
        ROOT / 'apps/documents/index.html': ('../../shared/ui-density.css', '../../shared/ui-density.js'),
        ROOT / 'apps/spreadsheets/index.html': ('../../shared/ui-density.css', '../../shared/ui-density.js'),
        ROOT / 'apps/presentations/index.html': ('../../shared/ui-density.css', '../../shared/ui-density.js'),
        ROOT / 'apps/pdf/index.html': ('../../shared/ui-density.css', '../../shared/ui-density.js'),
        ROOT / 'apps/epub/index.html': ('../../shared/ui-density.css', '../../shared/ui-density.js'),
        ROOT / 'apps/txt/page.template.html': ('../../shared/ui-density.css', '../../shared/ui-density.js'),
    }
    for path, markers in entries.items():
        text = path.read_text(encoding='utf-8')
        for marker in markers:
            require(text, marker, f'Density entry integration: {path.relative_to(ROOT)}')

    service_worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
    require(service_worker, '"./shared/ui-density.js"', 'Density offline JS')
    require(service_worker, '"./shared/ui-density.css"', 'Density offline CSS')

    stage_web = (ROOT / 'desktop/scripts/stage_web.py').read_text(encoding='utf-8')
    require(stage_web, 'ROOT_DIRS = ("assets", "apps", "shared")', 'Desktop staging must include shared runtime')

    probe = r'''
const fs=require('fs');
const vm=require('vm');
const path=process.argv[1];
vm.runInThisContext(fs.readFileSync(path,'utf8'),{filename:path});
const api=globalThis.InkDOSUiDensity;
if(!api)throw new Error('InkDOSUiDensity API missing');
const out={auto:api.resolve('auto'),mobile:api.resolve('mobile'),set:api.set('mobile'),preference:api.preference,effective:api.effective};
process.stdout.write(JSON.stringify(out));
'''
    completed = subprocess.run(['node', '-e', probe, str(JS)], cwd=ROOT, check=True, text=True, capture_output=True)
    result = json.loads(completed.stdout)
    expected = {key: 'desktop' for key in ('auto', 'mobile', 'set', 'preference', 'effective')}
    if result != expected:
        raise AssertionError(f'Density resolution mismatch: {result!r}')

    print('Desktop-only interface density contract: OK')


if __name__ == '__main__':
    main()
