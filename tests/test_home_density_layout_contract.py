#!/usr/bin/env python3
"""The Home and the workspaces offer no interface-density choice (owner, 2026-10-10): the Auto / Desktop / Smartphone
control, its icons and its Home layout rules are gone (tests/test_home_density_layout_browser.py checks the page)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'shared' / 'ui-density.js').read_text(encoding='utf-8')
CSS = (ROOT / 'shared' / 'ui-density.css').read_text(encoding='utf-8')
SETTINGS = (ROOT / 'shared' / 'localization' / 'settings-strip.js').read_text(encoding='utf-8')


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f'{label}: forbidden {needle!r}')


def main() -> None:
    for needle in ('buttonFor(', 'densityIcon(', 'installControl', 'data-inkdos-density'):
        forbid(JS, needle, 'Density control code')
    for needle in ('.home-density-control', '.inkdos-density-icon', '.inkdos-density-control'):
        forbid(CSS, needle, 'Density control CSS')
    forbid(SETTINGS, "['mobile','Smartphone']", 'Interface section of the Settings menu')
    print('Home without a density choice contract: OK')


if __name__ == '__main__':
    main()
