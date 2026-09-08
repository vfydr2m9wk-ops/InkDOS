#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "apps" / "pdf"

def text(path):
    return path.read_text(encoding="utf-8")

def main():
    app = text(PDF / "app.js")
    editor = text(PDF / "pdfjs" / "editor-adapter.js")
    nav = text(PDF / "ui" / "navigation-controller.js")
    layout = text(PDF / "view" / "page-layout.js")
    commands = text(PDF / "ui" / "command-controller.js")
    registry = text(PDF / "runtime" / "commands" / "command-registry.js")
    bindings = text(PDF / "ui" / "command-bindings.js")
    rail = text(PDF / "ui" / "toolbar-rail.js")
    page_ui = text(PDF / "ui" / "page-tools.js")
    page_runtime = text(PDF / "features" / "page-tools" / "page-tools-runtime.js")
    actions = {
        "move": text(PDF / "features" / "page-tools" / "actions" / "move-page.js"),
        "rotate": text(PDF / "features" / "page-tools" / "actions" / "rotate-page.js"),
        "delete": text(PDF / "features" / "page-tools" / "actions" / "delete-page.js"),
        "extract": text(PDF / "features" / "page-tools" / "actions" / "extract-page.js"),
        "split": text(PDF / "features" / "page-tools" / "actions" / "split-pdf.js"),
        "merge": text(PDF / "features" / "page-tools" / "actions" / "merge-pdfs.js"),
    }

    assert "editingstateschanged" in editor
    assert "annotationeditorstateschanged" in editor
    assert "DEFAULT_TAB='outline'" in nav
    assert "open(DEFAULT_TAB)" in nav
    assert "userScrollEpoch" in layout
    assert "sameMetrics" in layout
    assert "userEpoch===this.userScrollEpoch" in layout
    assert "scrollIntoView" not in layout
    assert "runtime/commands/command-registry.js" in app
    assert "ui/command-bindings.js" in app
    assert "ui/toolbar-rail.js" in app
    assert "features/page-tools/page-tools-runtime.js" in app
    for name in ("move-page.js","rotate-page.js","delete-page.js","extract-page.js","split-pdf.js","merge-pdfs.js"):
        assert name in app
    assert "function installToolbarRail" not in app
    assert "NS.ToolbarRail" in rail
    assert "NS.CommandRegistry" in registry
    assert "bindElement" in registry
    assert "history.undo" in commands and "history.redo" in commands
    assert "annotation.delete" in commands
    assert "$('undoBtn').onclick" not in commands
    assert "$('redoBtn').onclick" not in commands
    assert "$('deleteAnnotationBtn').onclick" not in commands
    assert "undoBtn:'history.undo'" in bindings
    assert "deleteAnnotationBtn:'annotation.delete'" in bindings

    # Page Tools must be a command-bound UI shell, not an implementation bucket.
    for command in ("pdf.pages.move","pdf.pages.rotate","pdf.pages.delete","pdf.pages.extract","pdf.pages.split","pdf.pages.merge.choose","pdf.pages.merge.files"):
        assert command in page_ui
    for forbidden in ("PageToolsEngine.movePage","PageToolsEngine.rotatePage","PageToolsEngine.deletePage","PageToolsEngine.extractPages","PageToolsEngine.splitAfter","PageToolsEngine.merge"):
        assert forbidden not in page_ui
    assert "snapshotCurrent" not in page_ui
    assert "verifyPdf" not in page_ui
    assert "PageToolsRuntime" in page_runtime
    expected = {
        "move": "PageToolsEngine.movePage",
        "rotate": "PageToolsEngine.rotatePage",
        "delete": "PageToolsEngine.deletePage",
        "extract": "PageToolsEngine.extractPages",
        "split": "PageToolsEngine.splitAfter",
        "merge": "PageToolsEngine.merge",
    }
    for key, needle in expected.items():
        assert needle in actions[key], f"{key} action lost its isolated engine call"
    # An individual action must not import/mention sibling action namespaces.
    action_names = ("PageMoveAction","PageRotateAction","PageDeleteAction","PageExtractAction","PageSplitAction","PageMergeAction")
    for key, source in actions.items():
        own = {"move":"PageMoveAction","rotate":"PageRotateAction","delete":"PageDeleteAction","extract":"PageExtractAction","split":"PageSplitAction","merge":"PageMergeAction"}[key]
        assert own in source
        for other in action_names:
            if other != own:
                assert other not in source

    print("PDF stability/static isolation contract passed.")

if __name__ == "__main__":
    main()
