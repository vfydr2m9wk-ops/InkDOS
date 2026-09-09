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
    tools = read("apps/presentations/ui/ppt-p2-tools.js")
    ui = read("apps/presentations/ui/ppt-p2-table-tools-ui.js")
    writer = read("apps/presentations/io/pptx-preservation-writer.js")

    commands = (
        "table.cell.text.set",
        "table.row.insert",
        "table.row.delete",
        "table.column.insert",
        "table.column.delete",
        "table.cells.merge",
        "table.cells.split",
        "table.cell.fill.set",
        "table.cell.border.set",
        "table.style.set",
    )
    for command in commands:
        require(tools, f"commands.register('{command}'", "Tables semantic command registry")

    for command in commands[1:]:
        require(ui, f'data-command="{command}"', "Table Tools command binding metadata")

    for kind in (
        "row.insert",
        "row.delete",
        "column.insert",
        "column.delete",
        "cells.merge",
        "cells.split",
        "cell.fill",
        "cell.border",
        "table.style",
    ):
        require(writer, f"kind==='{kind}'", "Tables package-preservation replay")

    require(tools, "session.sourceKind==='pptx'", "Tables writable-source gate")
    require(tools, "!!table?.pptP2Imported", "Tables mapped-import gate")
    require(ui, "app.executeCommand(command,...args)", "Table Tools command dispatch")
    require(ui, "document.addEventListener('pointerdown',rememberCell,true)", "Table Tools pointer selection boundary")
    require(ui, "document.addEventListener('focusin',rememberCell,true)", "Table Tools focus selection boundary")
    require(writer, "sourceBaselineSlides", "Tables source-baseline preservation")

    # Table controls remain a projection of semantic commands. They may not
    # acquire package-writing or history ownership merely to expand feature count.
    for unsafe in (
        "history.transact",
        "PptxPreservationWriter",
        "PptP2Package",
        "JSZip",
        "DOMParser",
    ):
        forbid(ui, unsafe, "Tables UI isolation")

    # General arbitrary table-package rewriting remains deliberately outside
    # this completion checkpoint; supported mutations must continue through
    # the validated operation log and imported source mapping.
    require(writer, "pptP2StructureOps", "Tables supported-operation log")
    require(writer, "sourceRef", "Tables source identity")

    print("PPT-P2 Tables closure contract: OK")


if __name__ == "__main__":
    main()
