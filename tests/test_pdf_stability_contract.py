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

    print("PDF stability/static isolation contract passed.")

if __name__ == "__main__":
    main()
