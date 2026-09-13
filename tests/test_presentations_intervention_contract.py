#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACE = (ROOT / 'apps/presentations/view/slide-surface.js').read_text(encoding='utf-8')
CSS = (ROOT / 'apps/presentations/view/presentation-surface.css').read_text(encoding='utf-8')

# Intervention contract: object selection/movement must be distinct from text editing.
for token in [
    'editingTextId',
    'enterTextEdit',
    'exitTextEdit',
    "e.key==='Escape'",
    "dataset.textEditing",
]:
    assert token in SURFACE, f'Presentations intervention contract missing: {token}'

# Direct object-body movement must share the existing gesture/history path.
assert 'startObjectMove' in SURFACE, 'Selected objects cannot start a direct body drag.'
assert "kind:'move'" in SURFACE, 'Direct object drag does not reuse the move gesture.'
assert "history.commitFromBefore(label,before)" in SURFACE, 'Gesture history contract was lost.'

# Text content may overflow its own nominal box, but the slide itself remains clipped.
assert '.slide-canvas' in CSS and 'overflow:hidden' in CSS, 'Slide boundary clipping must remain.'
assert '.rich-text-content{width:100%;min-height:1em;outline:0;white-space:pre-wrap;overflow:visible}' in CSS, (
    'Editable rich text is still hard-clipped inside its nominal text box.'
)
assert '.slide-textbox.text-editing' in CSS, 'Text-edit mode needs a distinct visual/state selector.'

print('Presentations intervention static contract passed.')
