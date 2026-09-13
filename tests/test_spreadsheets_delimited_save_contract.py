#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    save_controller = (ROOT / 'apps/spreadsheets/io/save-controller.js').read_text(encoding='utf-8')
    file_delivery = (ROOT / 'apps/spreadsheets/io/file-delivery.js').read_text(encoding='utf-8')

    require(save_controller, 'NS.DelimitedText.serialize', 'Delimited normal-save routing')
    require(save_controller, "session.sourceKind==='csv'||session.sourceKind==='tsv'", 'Delimited source-kind routing')
    require(save_controller, "session.sourceKind==='tsv'?'\\t':','", 'CSV/TSV delimiter preservation')
    require(save_controller, 'bom:session.book?.delimitedMeta?.bom', 'Delimited BOM preservation')
    require(save_controller, 'encoding:session.book?.delimitedMeta?.encoding', 'Delimited encoding preservation')
    require(save_controller, 'sourceKind:session.sourceKind', 'Delivery source-kind propagation')

    require(file_delivery, "sourceKind==='csv'?'.csv':sourceKind==='tsv'?'.tsv':'.xlsx'", 'Delivery extension preservation')
    require(file_delivery, "sourceKind==='csv'?'text/csv;charset=utf-8':sourceKind==='tsv'?'text/tab-separated-values;charset=utf-8'", 'Delivery MIME preservation')
    require(file_delivery, "description:sourceKind==='csv'?'CSV file':sourceKind==='tsv'?'TSV file':'Excel workbook'", 'Save-picker format identity')

    print('Spreadsheets CSV/TSV same-format save contract: OK')


if __name__ == '__main__':
    main()
