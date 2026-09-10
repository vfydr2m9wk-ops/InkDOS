#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
state = json.loads((ROOT / 'FUNCTIONAL_STATE.json').read_text(encoding='utf-8'))
current = state['currentPhase']
if current == {'id': 'XLS-S1', 'workspace': 'spreadsheets', 'status': 'active'}:
    assert 'XLS-S1' not in state['completedPhases']
elif current == {'id': 'XLS-S2', 'workspace': 'spreadsheets', 'status': 'active'}:
    assert 'XLS-S1' in state['completedPhases']
else:
    raise AssertionError(f'unexpected spreadsheet roadmap state: {current!r}')
assert 'PPT-P2' in state['completedPhases']

editor = (ROOT / 'apps/spreadsheets/engine/workbook-editor.js').read_text(encoding='utf-8')
for needle in (
    'rewriteWorkbookFormulas',
    'snapshotExternalFormulas',
    'restoreExternalFormulas',
    "axis:'row'",
    "axis:'column'",
    'formulaHistory:true',
    "return'#REF!'",
    "next==='('",
):
    assert needle in editor, needle
assert editor.count('rewriteWorkbookFormulas(this.session.book,s') == 4
assert editor.count('formulaHistory:true') == 4

controller = (ROOT / 'apps/spreadsheets/ui/editor-controller.js').read_text(encoding='utf-8')
for command in ('structure.insertRow', 'structure.insertColumn', 'structure.deleteRows', 'structure.deleteColumns'):
    assert command in controller, command

print('XLS-S1 structural formula contract: OK')
