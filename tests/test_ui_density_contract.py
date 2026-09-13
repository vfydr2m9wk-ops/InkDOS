#!/usr/bin/env python3
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
    if not JS.is_file():
        raise AssertionError('Shared adaptive density authority missing: shared/ui-density.js')
    if not CSS.is_file():
        raise AssertionError('Shared adaptive density stylesheet missing: shared/ui-density.css')

    js = JS.read_text(encoding='utf-8')
    css = CSS.read_text(encoding='utf-8')
    for needle in [
        "inkdos2:ui-density",
        "'auto'",
        "'desktop'",
        "'mobile'",
        '900',
        "(hover: hover) and (pointer: fine)",
        'data-ui-density',
        'installControl',
        'localStorage',
    ]:
        require(js, needle, 'Adaptive density authority')
    for forbidden in ['fetch(', 'XMLHttpRequest', 'WebSocket', 'sendBeacon']:
        forbid(js, forbidden, 'Adaptive density must stay local-only')

    require(css, '[data-ui-density="desktop"]', 'Desktop density CSS')
    require(css, '[data-ui-density="mobile"]', 'Mobile density CSS')
    require(css, '--control:', 'Shared density tokens')

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
            require(text, marker, f'Adaptive density entry integration: {path.relative_to(ROOT)}')

    service_worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
    require(service_worker, '"./shared/ui-density.js"', 'Adaptive density offline JS')
    require(service_worker, '"./shared/ui-density.css"', 'Adaptive density offline CSS')

    probe = r'''
const fs=require('fs');
const vm=require('vm');
const path=process.argv[1];
vm.runInThisContext(fs.readFileSync(path,'utf8'),{filename:path});
const api=globalThis.InkDOSUiDensity;
if(!api)throw new Error('InkDOSUiDensity API missing');
if(typeof api.resolve!=='function')throw new Error('resolve() missing');
const out={
  desktop:api.resolve('auto',{width:1360,finePointer:true}),
  narrow:api.resolve('auto',{width:899,finePointer:true}),
  coarse:api.resolve('auto',{width:1360,finePointer:false}),
  forcedDesktop:api.resolve('desktop',{width:400,finePointer:false}),
  forcedMobile:api.resolve('mobile',{width:1600,finePointer:true}),
  invalid:api.resolve('bad-value',{width:1360,finePointer:true})
};
process.stdout.write(JSON.stringify(out));
'''
    completed = subprocess.run(
        ['node', '-e', probe, str(JS)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)
    expected = {
        'desktop': 'desktop',
        'narrow': 'mobile',
        'coarse': 'mobile',
        'forcedDesktop': 'desktop',
        'forcedMobile': 'mobile',
        'invalid': 'desktop',
    }
    if result != expected:
        raise AssertionError(f'Adaptive density resolution mismatch: {result!r}')

    print('Adaptive interface density contract: OK')


if __name__ == '__main__':
    main()
