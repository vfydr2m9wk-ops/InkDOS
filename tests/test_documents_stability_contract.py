#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BIND=(ROOT/'apps/documents/ui/command-controller.js').read_text(encoding='utf-8')
CMD=(ROOT/'apps/documents/runtime/commands/document-commands.js').read_text(encoding='utf-8')
APP=(ROOT/'apps/documents/app.js').read_text(encoding='utf-8')
NAV=(ROOT/'apps/documents/ui/navigation-panel.js').read_text(encoding='utf-8')
SW=(ROOT/'service-worker.js').read_text(encoding='utf-8')

for token in [
    "const registry=new Map()",
    "function register(id,handler)",
    "function execute(id,...args)",
    "register('file.new'",
    "register('edit.undo'",
    "register('format.bold'",
    "register('insert.table'",
    "register('panel.search'",
    "navigation.openPanel('searchPanel')",
]:
    assert token in CMD, f'Documents semantic command layer missing: {token}'

for token in [
    "commands.execute(id,...args)",
    "bindClick('undoBtn','edit.undo')",
    "bindClick('redoBtn','edit.redo')",
    "bindClick('newMenuBtn','file.new')",
    "bindClick('openMenuBtn','file.open')",
    "bindClick('saveMenuBtn','file.save')",
    "execute(e.shiftKey?'edit.redo':'edit.undo')",
    "executeCommand:execute",
]:
    assert token in BIND, f'Documents UI binding layer missing: {token}'

for forbidden in [
    "const registry=new Map()",
    "editor.restoreHistory(editor.historyIndex-1)",
    "editor.restoreHistory(editor.historyIndex+1)",
    "register('format.",
    "register('file.",
]:
    assert forbidden not in BIND, f'Command semantics leaked back into UI bindings: {forbidden}'

for forbidden in [
    "document.getElementById",
    "document.querySelector",
    ".onclick",
    "generalMenu",
    "contextMenu",
]:
    assert forbidden not in CMD, f'UI ownership leaked into semantic command layer: {forbidden}'

assert "loadScript('runtime/commands/document-commands.js'" in APP, 'Documents semantic command module is not bootstrapped locally'
assert "NS.DocumentCommands.create" in APP and "commandRegistry.install()" in APP, 'Documents app does not own semantic command lifecycle'
assert "./apps/documents/runtime/commands/document-commands.js" in SW, 'Documents semantic command module missing from offline shell'
assert "function openPanel(panelId)" in NAV, 'Navigation module lacks explicit panel command contract'
assert "openPanel,installTabs" in NAV, 'Navigation panel contract is not exported'
print('Documents semantic command / UI binding isolation contract passed.')
