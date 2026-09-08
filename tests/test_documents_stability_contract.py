#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'apps/documents/ui/command-controller.js').read_text(encoding='utf-8')
NAV=(ROOT/'apps/documents/ui/navigation-panel.js').read_text(encoding='utf-8')

required=[
    "const registry=new Map()",
    "function register(id,handler)",
    "function execute(id,...args)",
    "bindClick('undoBtn','edit.undo')",
    "bindClick('redoBtn','edit.redo')",
    "bindClick('newMenuBtn','file.new')",
    "bindClick('openMenuBtn','file.open')",
    "bindClick('saveMenuBtn','file.save')",
    "execute('file.save')",
    "execute(e.shiftKey?'edit.redo':'edit.undo')",
    "executeCommand:execute",
    "navigation.openPanel('searchPanel')",
]
missing=[token for token in required if token not in SRC]
assert not missing, f'Documents command isolation contract missing: {missing}'
for forbidden in [
    "$('undoBtn').onclick=()=>editor.restoreHistory",
    "$('redoBtn').onclick=()=>editor.restoreHistory",
    "$('saveMenuBtn').onclick=()=>",
    "$('openMenuBtn').onclick=()=>",
    "$('newMenuBtn').onclick=()=>",
    "document.querySelector('[data-panel=\"searchPanel\"]')?.click()",
]:
    assert forbidden not in SRC, f'Direct control/function coupling remains: {forbidden}'
assert "function openPanel(panelId)" in NAV, 'Navigation module lacks explicit panel command contract'
assert "openPanel,installTabs" in NAV, 'Navigation panel contract is not exported'
print('Documents command/control isolation contract passed.')
