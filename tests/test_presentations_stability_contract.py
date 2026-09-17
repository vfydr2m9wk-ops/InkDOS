#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (ROOT / 'apps/presentations/ui/command-controller.js').read_text(encoding='utf-8')
BINDINGS = (ROOT / 'apps/presentations/ui/editing-controller.js').read_text(encoding='utf-8')
PANEL = (ROOT / 'apps/presentations/ui/slide-panel-controller.js').read_text(encoding='utf-8')
APP = (ROOT / 'apps/presentations/app.js').read_text(encoding='utf-8')
HTML = (ROOT / 'apps/presentations/index.html').read_text(encoding='utf-8')
P1_TOOLS = (ROOT / 'apps/presentations/ui/ppt-p1-tools.js').read_text(encoding='utf-8')

for token in [
    "const registry=new Map()",
    "function register(id,handler",
    "function execute(id,...args)",
    "register('history.undo'",
    "register('history.redo'",
    "register('panel.toggle'",
    "register('slide.add'",
    "register('slide.duplicate'",
    "register('slide.delete'",
    "register('slide.move'",
    "register('edit.insertText'",
    "register('navigation.to'",
    "register('navigation.previous'",
    "register('navigation.next'",
]:
    assert token in COMMANDS, f'Presentations command registry contract missing: {token}'

for forbidden in [
    "$('undoBtn').click()",
    "$('redoBtn').click()",
]:
    assert forbidden not in COMMANDS, f'Keyboard command still depends on a toolbar control: {forbidden}'

for token in [
    "commands.execute('slide.move'",
    "bindClick('undoBtn','history.undo')",
    "bindClick('redoBtn','history.redo')",
    "bindClick('slidePanelBtn','panel.toggle')",
    "bindClick('addSlideBtn','slide.add')",
    "bindClick('duplicateSlideBtn','slide.duplicate')",
    "bindClick('deleteSlideBtn','slide.delete')",
    "bindClick('insertTextBtn','edit.insertText')",
    "bindClick('prevSlideBtn','navigation.previous')",
    "bindClick('nextSlideBtn','navigation.next')",
    "panel.isOpen",
    "setAttribute('aria-expanded',String(panel.isOpen))",
]:
    assert token in BINDINGS, f'Presentations binding/projection contract missing: {token}'

for forbidden in [
    "history.transact(",
    "history.undo()",
    "history.redo()",
    "session.addSlide()",
    "session.duplicateCurrent()",
    "session.deleteCurrent()",
    "session.moveCurrent(",
    "session.addText()",
]:
    assert forbidden not in BINDINGS, f'Editing semantics leaked into control binding layer: {forbidden}'

assert 'slidePanelBtn' not in PANEL, 'Slide panel state still depends on a toolbar control id'
assert "workspace.dataset.panelOpen=String(open)" in PANEL, 'Slide panel no longer projects its authoritative open state to workspace layout'
assert "editor.sync()" in COMMANDS, 'Panel command does not request visual state projection after semantic toggle'
assert "onNavigate:index=>{commands?.execute('navigation.to',index)" in APP, 'Thumbnail navigation does not route through the Presentations command registry'
assert "session.setCurrentByIndex(index)" not in APP, 'App bootstrap still owns duplicate slide navigation semantics'
assert "editor.install(commands)" in APP, 'Editing bindings are not wired to the command registry'
assert "executeCommand:commands.execute" in APP, 'Presentations debug API does not expose independent command execution'
assert "hasCommand:commands.has" in APP and "listCommands:commands.list" in APP, 'Presentations command registry is not introspectable for regression tests'

# Prompt 2 Stage B thumbnail fidelity: the paper already carries each slide's
# true aspect ratio, so object projection must also be relative to that paper.
# A fixed 160 px geometry basis diverges as CSS resizes landscape/portrait
# thumbnail papers and can crop or misplace objects on real device layouts.
assert "paper.style.aspectRatio=`${slide.widthEmu}/${slide.heightEmu}`" in PANEL, 'Thumbnail paper no longer follows the source slide aspect ratio'
assert "const pw=160" not in PANEL, 'Thumbnail object geometry still depends on a hard-coded 160px paper width'
assert "o.x/slide.widthEmu*100" in PANEL, 'Thumbnail horizontal geometry is not projected relative to the slide width'
assert "o.y/slide.heightEmu*100" in PANEL, 'Thumbnail vertical geometry is not projected relative to the slide height'

# Prompt 2 Stage B approved toolbar redesign: keep stable command IDs while
# exposing user-facing semantic groups and semantic/current-color affordances.
for group_id, label in (
    ('pptToolbarSlides', 'Slides'),
    ('pptToolbarInsert', 'Insert'),
    ('pptToolbarText', 'Text formatting'),
    ('pptToolbarObjectStyle', 'Object style'),
):
    assert f'id="{group_id}"' in HTML, f'Presentations semantic toolbar host missing: {group_id}'
    assert f'aria-label="{label}"' in HTML, f'Presentations semantic toolbar label missing: {label}'

for control_id in (
    'addSlideBtn', 'duplicateSlideBtn', 'deleteSlideBtn', 'insertTextBtn',
    'fontSize', 'boldBtn', 'italicBtn', 'alignSelect', 'zoomMenuBtn', 'presentBtn',
):
    assert HTML.count(f'id="{control_id}"') == 1, f'Presentations toolbar control must remain unique: {control_id}'

for control_id in (
    'pptP1ImageBtn', 'pptP1Shape', 'pptP1TextColor', 'pptP1Fill',
    'pptP1Border', 'pptP1Bullets', 'pptP1Layout',
):
    assert control_id in P1_TOOLS, f'Existing P1 control id was lost during toolbar redesign contract: {control_id}'

assert 'ppt-p1-color-icon' in P1_TOOLS, 'Presentations color controls lack semantic icon structure'
assert 'ppt-p1-color-swatch' in P1_TOOLS, 'Presentations color controls lack current-color indicator'
assert '<svg' in P1_TOOLS, 'Presentations color controls do not use semantic SVG iconography'
assert "'●'" not in P1_TOOLS and "'○'" not in P1_TOOLS, 'Presentations still exposes raw dot glyph color affordances'

print('Presentations command/control, thumbnail fidelity, and toolbar semantic contract passed.')