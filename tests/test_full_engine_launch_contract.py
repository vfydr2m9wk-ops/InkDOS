#!/usr/bin/env python3
"""Every file opens in its InkDOS workspace first (no Light/Full switch). ONLYOFFICE is offered on request
(InkDOSFileLaunch.openInOffice): the editors of InkDOS Office are framed in their embed mode on their own origin and
driven only by InkDOS (embedOrigin). Every workspace carries the same launch bridge and may frame that origin."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICE = 'https://inkdos-tools.github.io'
APPS = ('documents', 'spreadsheets', 'presentations', 'pdf', 'txt', 'epub')


def main() -> None:
    copies = {(ROOT / f'apps/{app}/runtime/platform/file-launch.js').read_text(encoding='utf-8') for app in APPS}
    assert len(copies) == 1, 'the launch bridge copies must stay identical'
    bridge = copies.pop()
    assert f"OFFICE_ORIGIN='{OFFICE}'" in bridge
    assert 'routeFile(file){if(!file)return false;return lightRoute(file)}' in bridge, 'every file opens in InkDOS first'
    assert "getItem('inkdos2:engine')" not in bridge, 'no Light/Full switch'
    assert 'openInOffice:file=>OFFICE_EXT.has(extension(file?.name))&&openInOffice(file)' in bridge
    assert "searchParams.set('embed','1')" in bridge and "searchParams.set('embedOrigin',g.location.origin)" in bridge
    # the file goes only to the office origin, and only messages from that frame are read
    assert "postMessage({id:'inkdos-launch',type:'document:open-file',payload:{file,fileName:file.name}},OFFICE_ORIGIN)" in bridge
    assert 'event.origin!==OFFICE_ORIGIN||event.source!==frame.contentWindow' in bridge
    assert "'*'" not in bridge, 'no wildcard target origin'
    exts = set(re.search(r"OFFICE_EXT=new Set\(\[([^\]]*)\]\)", bridge).group(1).replace("'", '').split(','))
    assert {'docx', 'doc', 'odt', 'rtf', 'xlsx', 'xls', 'ods', 'csv', 'pptx', 'ppt', 'odp'} <= exts, exts
    assert not (ROOT / 'assets/engine-switch.js').exists() and 'engine-switch' not in (ROOT / 'index.html').read_text(encoding='utf-8')
    for app in APPS:
        html = (ROOT / f'apps/{app}/index.html').read_text(encoding='utf-8')
        assert f"frame-src 'self' {OFFICE}" in html, app
    print('Launch route (InkDOS first, ONLYOFFICE on request): OK')


if __name__ == '__main__':
    main()
