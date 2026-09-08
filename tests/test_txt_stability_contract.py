#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'apps' / 'txt'


def require(text: str, needle: str, message: str) -> None:
    if needle not in text:
        raise SystemExit(message)


def main() -> None:
    runtime_files = [
        APP / 'app.js',
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
    controls = (APP / 'ui' / 'txt-controls.js').read_text(encoding='utf-8')
    editor = (APP / 'editor' / 'editor-controller.js').read_text(encoding='utf-8')
    files = (APP / 'io' / 'txt-file-controller.js').read_text(encoding='utf-8')

    for needle in [
        '<!-- STYLES -->',
        '<!-- SCRIPT apps/txt/editor/editor-controller.js -->',
        '<!-- SCRIPT apps/txt/io/txt-file-controller.js -->',
        '<!-- SCRIPT apps/txt/ui/txt-controls.js -->',
        '<!-- SCRIPT apps/txt/editor/t1-essentials.js -->',
        '<!-- SCRIPT apps/txt/editor/t2-xml-tools.js -->',
        '<!-- SCRIPT apps/txt/app.js -->',
        "document.body.dataset.runtimeReady",
    ]:
        require(template, needle, f'Plain Text template contract missing: {needle}')

    if '<!-- SCRIPT ' in bundle or '<!-- STYLES -->' in bundle:
        raise SystemExit('Plain Text generated bundle still contains unexpanded source markers')
    require(bundle, "document.documentElement.dataset.inkdosBundle='inline-d3'", 'Plain Text bundle identity marker missing')

    for needle in [
        'NS.TxtControls.create()',
        'NS.TxtEditorController.create',
        'NS.TxtFileController.create',
        'NS.TxtT1Essentials.create',
        'NS.TxtT2XmlTools.create',
        'NS.TxtAppDebug=Object.freeze',
        'files.initialize()',
    ]:
        require(app, needle, f'Plain Text bootstrap contract missing: {needle}')

    for needle in [
        'E.editor.addEventListener',
        'E.undoBtn.onclick=editor.doUndo',
        'E.redoBtn.onclick=editor.doRedo',
        'E.findBtn.onclick',
        "if(mod&&e.key.toLowerCase()==='s')",
        "if(mod&&e.key.toLowerCase()==='n')",
        "if(mod&&e.key.toLowerCase()==='o')",
    ]:
        require(controls, needle, f'Plain Text control baseline missing: {needle}')

    for needle in [
        'function doUndo()',
        'function doRedo()',
        'function markChanged()',
        'function setWrap(next)',
        'function setViewFont(size)',
        'state.history.push(E.editor.value)',
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
