#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'shared' / 'ui-density.js').read_text(encoding='utf-8')
CSS = (ROOT / 'shared' / 'ui-density.css').read_text(encoding='utf-8')


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f'{label}: forbidden {needle!r}')


def main() -> None:
    # Home exposes the requested Auto -> Desktop icon -> Smartphone icon order,
    # while keeping the internal persisted value `mobile` for compatibility.
    require(JS, "buttonFor('auto','Auto'", 'Home density order')
    require(JS, "buttonFor('desktop','Desktop'", 'Home density order')
    require(JS, "buttonFor('mobile','Smartphone'", 'Home density order')
    require(JS, "buttonFor('desktop','Desktop',{icon:true})", 'Desktop density icon request')
    require(JS, "buttonFor('mobile','Smartphone',{icon:true})", 'Smartphone density icon request')
    require(JS, "const glyph=densityIcon(mode)", 'Density icon rendering')

    # The Home menu must size controls from their content instead of forcing
    # three equal columns inside the narrow appearance popover.
    require(CSS, '.home-density-control{', 'Home density override')
    require(CSS, 'grid-template-columns:max-content max-content max-content', 'Home density content sizing')
    require(CSS, 'justify-content:end', 'Home density alignment')
    require(CSS, '.home-density-control button{', 'Home density button rule')
    require(CSS, 'white-space:nowrap', 'Home density labels')
    require(CSS, '.inkdos-density-icon{', 'Density icon sizing')
    require(CSS, 'flex:0 0 auto', 'Density icon stability')

    # Do not solve overlap with absolute positioning or fixed pixel widths.
    forbid(CSS, '.home-density-control{position:absolute', 'Home density layout')
    forbid(CSS, '.home-density-control button{width:', 'Home density button sizing')

    print('Home density layout contract: OK')


if __name__ == '__main__':
    main()
