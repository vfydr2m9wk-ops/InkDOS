#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    editor = (ROOT / 'apps/spreadsheets/ui/editor-controller.js').read_text(encoding='utf-8')
    formula_bar = (ROOT / 'apps/spreadsheets/ui/formula-bar.js').read_text(encoding='utf-8')

    # Delimited files may keep ordinary value edits/pastes in CSV/TSV, but formulas
    # and XLSX-only cell styling must require an explicit conversion first.
    require(editor, 'function cellNeedsXlsx', 'Semantic paste representability predicate')
    require(editor, 'function payloadNeedsXlsx', 'Semantic paste payload predicate')
    require(editor, "ensureXlsxFor('Paste formulas or formatting')", 'Semantic paste conversion guard')
    require(editor, "ensureXlsxFor('Paste formulas')", 'Plain-text formula paste guard')

    # Direct cell/formula-bar edits that create formulas must be guarded too.
    require(editor, 'async function commitValueGuarded', 'Direct formula-edit conversion guard')
    require(editor, "ensureXlsxFor('Formulas')", 'Formula conversion prompt')
    require(editor, 'beforeCommit:commitValueGuarded', 'Formula Bar guard wiring')
    require(formula_bar, 'beforeCommit', 'Formula Bar pre-commit hook')
    require(formula_bar, 'await beforeCommit?.(value)', 'Formula Bar awaits conversion decision')

    # Formula-producing operations and percentage formatting cannot remain in CSV/TSV.
    require(editor, "['sum','average','min','max','count','percent'].includes(kind)", 'Operation representability guard')
    require(editor, "ensureXlsxFor(kind==='percent'?'Percentage formatting':'Formulas')", 'Operation conversion prompt')

    print('Spreadsheets CSV/TSV formula and semantic-paste guards: OK')


if __name__ == '__main__':
    main()
