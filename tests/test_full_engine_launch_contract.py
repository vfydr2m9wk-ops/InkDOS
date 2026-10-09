#!/usr/bin/env python3
"""Full version (Home engine switch): a Word, Excel or PowerPoint file opened from the system goes to the ONLYOFFICE
editors of InkDOS Office, framed in their embed mode on their own origin and driven only by InkDOS (embedOrigin);
other formats, the Light version and the desktop app keep the InkDOS workspace. Every workspace carries the same
launch bridge, and the office workspaces may frame that origin."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICE = 'https://inkdos-tools.github.io'


def main() -> None:
    bridge = (ROOT / 'apps/documents/runtime/platform/file-launch.js').read_text(encoding='utf-8')
    assert f"OFFICE_ORIGIN='{OFFICE}'" in bridge
    assert "localStorage?.getItem('inkdos2:engine')==='complete'" in bridge, 'only the Full version'
    assert '!g.InkDOSDesktop' in bridge and "inkdosHost!=='tauri'" in bridge, 'not in the desktop app'
    assert "searchParams.set('embed','1')" in bridge and "searchParams.set('embedOrigin',g.location.origin)" in bridge
    # the file goes only to the office origin, and only messages from that frame are read
    assert "postMessage({id:'inkdos-launch',type:'document:open-file',payload:{file,fileName:file.name}},OFFICE_ORIGIN)" in bridge
    assert 'event.origin!==OFFICE_ORIGIN||event.source!==frame.contentWindow' in bridge
    assert "'*'" not in bridge, 'no wildcard target origin'
    exts = set(re.search(r"OFFICE_EXT=new Set\(\[([^\]]*)\]\)", bridge).group(1).replace("'", '').split(','))
    assert {'docx', 'doc', 'odt', 'rtf', 'xlsx', 'xls', 'ods', 'csv', 'pptx', 'ppt', 'odp'} <= exts, exts
    assert ('routeFile(file){if(!file)return false;if(fullEngine(file)&&openInOffice(file,lightRoute))return true;'
            'if(openInViewer(file,lightRoute,viewerPage(file)))return true;return lightRoute(file)}') in bridge
    assert "epub:'" not in bridge, 'EPUB books stay in the InkDOS EPUB reader'
    # iWork, PDF and text go to the InkDOS-tools viewers through the viewer protocol, origin-checked
    assert "postMessage({type:'inkdos-viewer-open',file},OFFICE_ORIGIN)" in bridge
    assert all(f"{ext}:'{page}'" in bridge for ext, page in (('pages', 'pnk/'), ('key', 'pnk/'), ('txt', 'txt/')))
    for app in ('documents', 'spreadsheets', 'presentations', 'pdf', 'txt', 'epub'):
        html = (ROOT / f'apps/{app}/index.html').read_text(encoding='utf-8')
        assert f"frame-src 'self' {OFFICE}" in html, app
    print('Full version launch route: OK')


if __name__ == '__main__':
    main()
