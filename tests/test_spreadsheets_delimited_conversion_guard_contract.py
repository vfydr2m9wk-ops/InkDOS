#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    session = (ROOT / 'apps/spreadsheets/engine/workbook-session.js').read_text(encoding='utf-8')
    editor = (ROOT / 'apps/spreadsheets/ui/editor-controller.js').read_text(encoding='utf-8')
    dialog = (ROOT / 'apps/spreadsheets/ui/session-dialog.js').read_text(encoding='utf-8')
    service_worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')

    require(session, 'convertToXlsx(){', 'WorkbookSession explicit conversion')
    require(session, "this.sourceKind='xlsx'", 'WorkbookSession conversion source kind')
    require(session, "safeName(this.fileName,'xlsx')", 'WorkbookSession conversion filename')

    require(editor, 'async function ensureXlsxFor', 'Delimited conversion guard')
    require(editor, "title:'Convert to XLSX?'", 'Delimited conversion warning')
    require(editor, "confirmLabel:'Convert to XLSX'", 'Explicit conversion action')
    require(editor, "registerGuarded('format.bold'", 'Formatting conversion guard')
    require(editor, "registerGuarded('format.merge'", 'Merge conversion guard')
    require(editor, "await ensureXlsxFor(kind==='column'?'Column width':'Row height')", 'Dimension conversion guard')
    require(editor, "if(!await ensureXlsxFor('Add worksheet'))return", 'Add-sheet conversion guard')
    require(editor, "if(!await ensureXlsxFor('Delete worksheet'))return", 'Delete-sheet conversion guard')

    require(dialog, "confirmLabel='Confirm'", 'Two-action confirmation label support')
    require(dialog, 'discard.hidden=true', 'Confirmation mode hides destructive discard action')
    require(dialog, "return result==='save'", 'Confirmation resolves only from the explicit confirm action')

    require(service_worker, '"./apps/spreadsheets/io/delimited-text.js"', 'CSV/TSV codec offline shell entry')

    print('Spreadsheets CSV/TSV explicit XLSX conversion guard contract: OK')


if __name__ == '__main__':
    main()
