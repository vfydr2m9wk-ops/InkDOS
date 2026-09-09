#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
state = json.loads((ROOT / 'FUNCTIONAL_STATE.json').read_text(encoding='utf-8'))
assert state['currentPhase'] == {'id': 'XLS-S1', 'workspace': 'spreadsheets', 'status': 'active'}
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
