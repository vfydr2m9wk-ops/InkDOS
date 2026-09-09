#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: forbidden {needle!r}")


def main() -> None:
    ui = read("apps/presentations/ui/ppt-p2-table-tools-ui.js")
    index = read("apps/presentations/index.html")
    service_worker = read("service-worker.js")

    require(ui, "app.hasCommand?.('table.style.set')", "Table Tools command readiness")
    require(ui, "app.executeCommand(command,...args)", "Table Tools command dispatch")
    require(ui, "app.p2Tools?.tableStructureEditable?.(table.id)", "Table Tools semantic capability query")
    require(ui, "app.session?.sourceKind==='pptx'&&table.pptP2Imported&&table.sourceRef", "Table Tools mapped-table gate")

    for command in (
        "table.cell.fill.set",
        "table.cell.border.set",
        "table.style.set",
        "table.row.insert",
        "table.row.delete",
        "table.column.insert",
        "table.column.delete",
        "table.cells.merge",
        "table.cells.split",
    ):
        require(ui, f'data-command="{command}"', "Table Tools command binding metadata")
        require(ui, f"execute('{command}'", "Table Tools command dispatch")

    # The control surface must not become a second feature implementation.
    for forbidden in (
        "history.transact",
        "pptP2StructureOps",
        "PptxPreservationWriter",
        "PptP2Package",
        "JSZip",
        "sourceBytes",
        "DOMParser",
    ):
        forbid(ui, forbidden, "Table Tools semantic isolation")

    tools_pos = index.index('src="ui/ppt-p2-tools.js"')
    table_ui_pos = index.index('src="ui/ppt-p2-table-tools-ui.js"')
    if table_ui_pos <= tools_pos:
        raise AssertionError("Table Tools UI must load after semantic PPT-P2 tools")

    require(service_worker, '"./apps/presentations/ui/ppt-p2-table-tools-ui.js"', "Table Tools offline shell")

    print("PPT-P2 Table Tools UI contract: OK")


if __name__ == "__main__":
    main()
