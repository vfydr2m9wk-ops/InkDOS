#!/usr/bin/env python3
"""Desktop, Full version: InkDOS Office (third-party ONLYOFFICE code on its own origin) opens only in office-* windows
that have no native access: no capability lists them, require_trusted_window refuses them, they may navigate only
within https://inkdos-tools.github.io, and InkDOS's own windows still cannot frame or navigate there (host CSP
unchanged). The Home and files opened from Windows reach those windows only through the two commands."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'desktop/src-tauri'


def main() -> None:
    main_rs = (SRC / 'src/main.rs').read_text(encoding='utf-8')
    capability = json.loads((SRC / 'capabilities/default.json').read_text(encoding='utf-8'))
    assert not any(w.startswith('office') for w in capability['windows']), capability['windows']
    assert 'label == "main" || label.starts_with("file-") || label.starts_with("workspace-")' in main_rs
    assert 'const OFFICE_HOST: &str = "inkdos-tools.github.io";' in main_rs
    assert 'url.scheme() == "https" && url.host_str() == Some(OFFICE_HOST)' in main_rs
    assert 'webview.label().starts_with("office-") && is_office_page(url)' in main_rs
    assert 'let label = format!("office-{}", OFFICE_WINDOW_SEQUENCE' in main_rs
    for command in ('inkdos_open_office', 'inkdos_open_office_file'):
        assert f'fn {command}(' in main_rs and f'            {command}' in main_rs, command
    # both commands are for InkDOS's own windows only
    for name in ('fn inkdos_open_office(', 'fn inkdos_open_office_file('):
        body = main_rs[main_rs.index(name):main_rs.index('\n}\n', main_rs.index(name))]
        assert 'require_trusted_window(&webview)?;' in body, name
    script = (SRC / 'src/office_open.js').read_text(encoding='utf-8')
    assert "location.origin !== 'https://inkdos-tools.github.io'" in script and "event.origin !== location.origin" in script
    assert "'*'" not in script
    host_csp = json.loads((SRC / 'tauri.conf.json').read_text(encoding='utf-8'))['app']['security']['csp']
    assert host_csp['frame-src'] == "'self'", 'InkDOS windows do not frame the office site'
    # files opened from Windows open in their InkDOS workspace first (no Light/Full switch any more)
    desktop_host = (ROOT / 'desktop/desktop-host.js').read_text(encoding='utf-8')
    assert 'inkdos_open_office_file' not in desktop_host and 'inkdos2:engine' not in desktop_host
    print('Desktop full version contract: OK')


if __name__ == '__main__':
    main()
