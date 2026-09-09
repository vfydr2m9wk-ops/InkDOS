#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> None:
    tools = read("apps/presentations/ui/ppt-p2-tools.js")
    writer = read("apps/presentations/io/pptx-preservation-writer.js")
    session = read("apps/presentations/engine/presentation-session.js")

    for command in ("table.cells.merge", "table.cells.split"):
        require(tools, f"commands.register('{command}'", "PPT-P2 table semantic command")
    for marker in (
        "function mergeTableCells",
        "function splitTableCells",
        "function tableStructureEditable(tableId)",
        "mappedTable(table)&&!hasMerge(table)",
        "cellPlainText(table.rows[r].cells[c])!==''",
        "leader.colSpan=rect.right-rect.left+1",
        "leader.rowSpan=rect.bottom-rect.top+1",
        "cell.hMerge=c>rect.left",
        "cell.vMerge=r>rect.top",
        "{kind:'cells.merge'",
        "{kind:'cells.split'",
    ):
        require(tools, marker, "PPT-P2 table merge/split model contract")

    for marker in (
        "function normalizedStructureOp",
        "kind==='cells.merge'",
        "kind==='cells.split'",
        "function domHasMerge",
        "leader.setAttribute('gridSpan',String(colSpan))",
        "leader.setAttribute('rowSpan',String(rowSpan))",
        "tc.setAttribute('hMerge','1')",
        "tc.setAttribute('vMerge','1')",
        "Table merge would discard non-empty source cell content.",
        "Table split target is not a merged source cell.",
        "applyDomStructureOps(doc,tbl,plan.ops)",
    ):
        require(writer, marker, "PPT-P2 table merge/split preservation contract")

    require(session, "if(obj.type==='table')delete obj.pptP2StructureOps", "PPT-P2 confirmed-save table baseline contract")
    print("PPT-P2 table merge/split static contract passed.")


if __name__ == "__main__":
    main()
