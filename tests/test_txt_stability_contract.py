#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'apps' / 'txt'


def require(text: str, needle: str, message: str) -> None:
    if needle not in text:
        raise SystemExit(message)


def forbid(text: str, needle: str, message: str) -> None:
    if needle in text:
        raise SystemExit(message)


def main() -> None:
    runtime_files = [
        APP / 'app.js',
        APP / 'commands' / 'txt-commands.js',
        APP / 'editor' / 'editor-controller.js',
        APP / 'editor' / 'outline-model.js',
        APP / 'editor' / 't1-essentials.js',
        APP / 'editor' / 't2-xml-tools.js',
        APP / 'history.js',
        APP / 'io' / 'txt-file-controller.js',
        APP / 'runtime' / 'frame' / 'app-frame.js',
        APP / 'runtime' / 'platform' / 'content-viewport-adapter.js',
        APP / 'runtime' / 'services' / 'file-delivery.js',
        APP / 'runtime' / 'services' / 'recovery-store.js',
        APP / 'state' / 'appearance.js',
        APP / 'state' / 'txt-state.js',
        APP / 'txt-codec.js',
        APP / 'txt-policy.js',
        APP / 'ui' / 'txt-controls.js',
    ]
    for path in runtime_files:
        subprocess.run(['node', '--check', str(path)], cwd=ROOT, check=True)

    subprocess.run(['python', 'scripts/build_txt_bundle.py', '--check'], cwd=ROOT, check=True)

    template = (APP / 'page.template.html').read_text(encoding='utf-8')
    bundle = (APP / 'index.html').read_text(encoding='utf-8')
    app = (APP / 'app.js').read_text(encoding='utf-8')
    commands = (APP / 'commands' / 'txt-commands.js').read_text(encoding='utf-8')
    controls = (APP / 'ui' / 'txt-controls.js').read_text(encoding='utf-8')
    editor = (APP / 'editor' / 'editor-controller.js').read_text(encoding='utf-8')
    t1 = (APP / 'editor' / 't1-essentials.js').read_text(encoding='utf-8')
    t2 = (APP / 'editor' / 't2-xml-tools.js').read_text(encoding='utf-8')
    files = (APP / 'io' / 'txt-file-controller.js').read_text(encoding='utf-8')

    for needle in [
        '<!-- STYLES -->',
        '<!-- SCRIPT apps/txt/editor/editor-controller.js -->',
        '<!-- SCRIPT apps/txt/io/txt-file-controller.js -->',
        '<!-- SCRIPT apps/txt/commands/txt-commands.js -->',
        '<!-- SCRIPT apps/txt/ui/txt-controls.js -->',
        '<!-- SCRIPT apps/txt/editor/t1-essentials.js -->',
        '<!-- SCRIPT apps/txt/editor/t2-xml-tools.js -->',
        '<!-- SCRIPT apps/txt/app.js -->',
        "TxtAppDebug?.commands",
        "execute('file.new')",
        "execute('file.open.request')",
        "document.body.dataset.runtimeReady",
    ]:
        require(template, needle, f'Plain Text template contract missing: {needle}')
    for forbidden in [
        "getElementById('newBtn')?.click()",
        "getElementById('openBtn')?.click()",
        "f?.addEventListener('change'",
    ]:
        forbid(template, forbidden, f'Plain Text start gate still delegates semantics through another control: {forbidden}')

    if '<!-- SCRIPT ' in bundle or '<!-- STYLES -->' in bundle:
        raise SystemExit('Plain Text generated bundle still contains unexpanded source markers')
    require(bundle, "document.documentElement.dataset.inkdosBundle='inline-d3'", 'Plain Text bundle identity marker missing')

    for needle in [
        'NS.TxtControls.create()',
        'NS.TxtEditorController.create',
        'NS.TxtFileController.create',
        'NS.TxtCommands.create',
        'NS.TxtT1Essentials.create({elements:E,state,editor,files,controls,commands})',
        'controls.bind({editor,files,state,commands}',
        'NS.TxtT2XmlTools.create({elements:E,state,editor,files,beforeOpen:()=>t1?.closeTools()})',
        'NS.TxtAppDebug=Object.freeze({state,commands',
        'files.initialize()',
    ]:
        require(app, needle, f'Plain Text bootstrap contract missing: {needle}')

    for needle in [
        "register('file.new'",
        "register('file.open.request'",
        "register('file.open'",
        "register('file.save'",
        "register('file.share'",
        "register('history.undo'",
        "register('history.redo'",
        "register('view.wrap.toggle'",
        "register('view.font.set'",
        "register('outline.indent'",
        "register('outline.list'",
        "register('selection.all'",
        "register('clipboard.copy'",
        "register('clipboard.paste'",
        'TXT_COMMAND_NOT_REGISTERED',
    ]:
        require(commands, needle, f'Plain Text semantic command contract missing: {needle}')
    for forbidden in ['getElementById', 'undoBtn', 'redoBtn', 'wrapBtn', 'saveBtn', 'shareBtn']:
        forbid(commands, forbidden, f'Plain Text semantic commands must not own control DOM: {forbidden}')

    for needle in [
        'E.editor.addEventListener',
        "E.undoBtn.onclick=()=>execute('history.undo')",
        "E.redoBtn.onclick=()=>execute('history.redo')",
        "E.wrap.onclick=()=>execute('view.wrap.toggle')",
        "E.outdent.onclick=()=>execute('outline.indent',-1)",
        "E.indent.onclick=()=>execute('outline.indent',1)",
        "E.findBtn.onclick=()=>execute('find.toggle')",
        "E.findClose.onclick=()=>execute('find.close')",
        "E.findNext.onclick=()=>execute('find.next',E.findInput.value)",
        "E.findPrev.onclick=()=>execute('find.prev',E.findInput.value)",
        "E.selectAll.onclick=()=>execute('selection.all')",
        "if(mod&&e.key.toLowerCase()==='s')",
        "execute('file.save')",
        "execute('file.new')",
        "execute('file.open.request')",
        "execute('find.open')",
    ]:
        require(controls, needle, f'Plain Text control binding contract missing: {needle}')
    for forbidden in [
        'E.undoBtn.onclick=editor.doUndo',
        'E.redoBtn.onclick=editor.doRedo',
        'E.wrap.onclick=()=>editor.setWrap',
        'E.newBtn.onclick=()=>{frameMenu.close();files.newDoc()',
        'E.findNext.onclick=()=>editor.find',
        'E.findPrev.onclick=()=>editor.find',
        'files.save().catch',
        'files.shareCurrent().catch',
    ]:
        forbid(controls, forbidden, f'Plain Text controls still own semantic behavior: {forbidden}')

    for needle in [
        "commands.register('find.open'",
        "commands.register('find.close'",
        "commands.register('find.toggle'",
        "commands.register('find.next'",
        "commands.register('find.prev'",
        "commands.register('replace.one'",
        "commands.register('replace.all'",
        'function find(step,query)',
        'function replaceOne(query,replacement)',
        'function replaceAll(query,replacement)',
        "document.addEventListener('inkdos:txt-view-policy',scheduleLineNumbers)",
    ]:
        require(t1, needle, f'Plain Text T1 semantic command contract missing: {needle}')
    for forbidden in [
        'E.findPrev.onclick=',
        'E.findNext.onclick=',
        "E.wrap.addEventListener('click'",
        "E.font.addEventListener('change'",
        "E.fontDown.addEventListener('click'",
        "E.fontUp.addEventListener('click'",
    ]:
        forbid(t1, forbidden, f'Plain Text T1 must not bind semantic view behavior to a specific control: {forbidden}')

    for needle in [
        'function create({elements:E,state,editor,files,beforeOpen=()=>{}}={})',
        'function open(){beforeOpen();syncUi()',
        'const sep=E.findbar.nextElementSibling;E.toolbar.insertBefore(ui.btn,sep||null)',
        "document.addEventListener('inkdos:txt-view-policy',refreshView)",
        '.t2-view{position:absolute;z-index:3;',
    ]:
        require(t2, needle, f'Plain Text T2 isolation contract missing: {needle}')
    for forbidden in [
        'textToolsMenu',
        'textToolsBtn',
        'lineNumberGutter',
        "E.wrap.addEventListener('click'",
        "E.font.addEventListener('change'",
        "E.fontDown.addEventListener('click'",
        "E.fontUp.addEventListener('click'",
    ]:
        forbid(t2, forbidden, f'Plain Text T2 must not depend on sibling/view control DOM: {forbidden}')

    for needle in [
        'function doUndo()',
        'function doRedo()',
        'function markChanged()',
        'function setWrap(next)',
        'function setViewFont(size)',
        'state.history.push(E.editor.value)',
        "document.dispatchEvent(new CustomEvent('inkdos:txt-view-policy'",
    ]:
        require(editor, needle, f'Plain Text editor baseline missing: {needle}')

    for needle in [
        'function initializeEmptyState()',
        'function newDoc()',
        'async function openFile(file)',
        'function buildExportSnapshot()',
        'C.decode(buf)',
        'C.encode(snapshot.text',
        'NS.TxtExportVerify.verify',
        'openBytes:async',
        'exportBytes:',
    ]:
        require(files, needle, f'Plain Text file/session baseline missing: {needle}')

    combined = '\n'.join(path.read_text(encoding='utf-8') for path in runtime_files)
    for sibling in ['apps/documents/', 'apps/pdf/', 'apps/presentations/', 'apps/spreadsheets/', 'apps/epub/']:
        if sibling in combined:
            raise SystemExit(f'Plain Text contains sibling-workspace runtime dependency: {sibling}')

    print('Plain Text stability static/syntax/bundle contract passed.')


if __name__ == '__main__':
    main()