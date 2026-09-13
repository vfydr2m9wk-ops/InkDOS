#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'apps/spreadsheets/app.js').read_text(encoding='utf-8')


def require(needle: str, label: str) -> None:
    if needle not in APP:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    require('authorizedUnload=false', 'Spreadsheets Home leave state')
    require('authorizedUnload=true;root.location.href=home.href', 'Authorized Home transition')
    require('if(authorizedUnload){authorizedUnload=false;return}', 'One-shot beforeunload bypass')
    require("if(leaving||!session.dirty)return;e.preventDefault()", 'Dirty Home interception')
    print('Spreadsheets authorized Home exit contract: OK')


if __name__ == '__main__':
    main()
