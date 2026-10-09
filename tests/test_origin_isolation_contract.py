#!/usr/bin/env python3
"""Origin isolation contract (security).

InkDOS is served from https://vfydr2m9wk-ops.github.io/InkDOS/. Every GitHub Pages site of that
account shares this origin and therefore InkDOS's storage (recovery drafts), offline cache and
windows. Third-party or experimental web code must live on another origin: the InkDOS-tools site is
https://inkdos-offic.pages.dev (a separate GitHub organization). See SECURITY.md, "Origin isolation".

Checked here:
- no shipped InkDOS file refers to a page of vfydr2m9wk-ops.github.io outside /InkDOS/;
- the Advanced tools catalog and the workspace viewers use the tools origin only;
- the pages may frame nothing but themselves and the tools origin.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INKDOS_HOST = 'vfydr2m9wk-ops.github.io'
TOOLS_ORIGIN = 'https://inkdos-offic.pages.dev'
SHIPPED = ('index.html', 'service-worker.js', 'manifest.webmanifest', 'assets', 'apps', 'shared', 'labs', 'desktop')
SKIP_PARTS = {'vendor', 'node_modules', 'target', 'gen', 'icons'}
TEXT = {'.html', '.js', '.mjs', '.css', '.json', '.webmanifest', '.rs', '.toml'}
URL = re.compile(r'(?:https?:)?//' + re.escape(INKDOS_HOST) + r'(/[^\s"\'<>)`\\]*)?')


def shipped_files():
    for name in SHIPPED:
        path = ROOT / name
        files = [path] if path.is_file() else (p for p in path.rglob('*') if p.is_file())
        for file in files:
            if file.suffix in TEXT and not SKIP_PARTS & set(file.relative_to(ROOT).parts):
                yield file


def main() -> None:
    problems = []
    for file in shipped_files():
        for match in URL.finditer(file.read_text(encoding='utf-8', errors='ignore')):
            path = match.group(1) or '/'
            if path not in ('/', '/InkDOS') and not path.startswith('/InkDOS/'):
                problems.append(f'{file.relative_to(ROOT)}: {match.group(0)}')
    assert not problems, ('InkDOS must not use other pages of its own origin; host them on a separate '
                          'origin (see SECURITY.md, "Origin isolation"):\n  ' + '\n  '.join(problems))

    spec = importlib.util.spec_from_file_location('generate_csp', ROOT / 'scripts' / 'generate_csp.py')
    csp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(csp)
    assert csp.TOOLS_ORIGIN == TOOLS_ORIGIN, csp.TOOLS_ORIGIN

    catalog = (ROOT / 'assets' / 'advanced-tools.js').read_text(encoding='utf-8')
    for href in re.findall(r"href:'([^']+)'", catalog):
        assert href.startswith('./') or href.startswith(TOOLS_ORIGIN + '/'), href
    for app in ('documents', 'spreadsheets', 'presentations'):
        viewer = (ROOT / 'apps' / app / 'io' / 'external-viewer.js').read_text(encoding='utf-8')
        assert f"'{TOOLS_ORIGIN}/InkDOS-tools/'" in viewer, app
        assert 'event.origin!==TOOLS_ORIGIN' in viewer and 'location.origin' not in viewer.split('TOOLS_ORIGIN=')[1].split(';')[0], app

    meta = re.compile(r'http-equiv="Content-Security-Policy" content="([^"]+)"')
    for page in [ROOT / 'index.html', *(ROOT / 'apps').glob('*/index.html'), ROOT / 'labs' / 'pdf' / 'index.html']:
        policy = meta.search(page.read_text(encoding='utf-8')).group(1)
        frame = next(d for d in policy.split(';') if d.strip().startswith('frame-src')).split()[1:]
        assert set(frame) <= {"'self'", "'none'", TOOLS_ORIGIN}, f'{page.relative_to(ROOT)}: frame-src {frame}'
    print('Origin isolation contract: OK')


if __name__ == '__main__':
    main()
