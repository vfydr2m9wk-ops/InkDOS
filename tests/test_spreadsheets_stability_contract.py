#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def main() -> None:
    index = read('apps/spreadsheets/index.html')
    app = read('apps/spreadsheets/app.js')
    frame = read('apps/spreadsheets/runtime/frame/frame-menu.js')
    editor_controller = read('apps/spreadsheets/ui/editor-controller.js')
    workbook_editor = read('apps/spreadsheets/engine/workbook-editor.js')
    workbook_session = read('apps/spreadsheets/engine/workbook-session.js')
    file_open = read('apps/spreadsheets/io/file-open-controller.js')
    save_controller = read('apps/spreadsheets/io/save-controller.js')
    package_validator = read('apps/spreadsheets/io/package-validator.js')
    xlsx_engine = read('apps/spreadsheets/io/xlsx-engine.js')
    xls_engine = read('apps/spreadsheets/io/xls-biff8-engine.js')
    service_worker = read('service-worker.js')

    # Key dependency boundaries must remain explicit and ordered. This is not a
    # fixed file-count contract; new natural responsibility modules may be inserted.
    ordered_scripts = [
        'io/package-validator.js',
        'io/worksheet-package.js',
        'io/xls-biff8-engine.js',
        'io/xlsx-engine.js',
        'runtime/frame/frame-menu.js',
        'engine/workbook-session.js',
        'engine/selection-model.js',
        'engine/history.js',
        'engine/formula/evaluator.js',
        'engine/workbook-editor.js',
        'view/grid-surface.js',
        'ui/editor-controller.js',
        'io/file-open-controller.js',
        'io/save-controller.js',
        'app.js',
    ]
    positions = []
    for script in ordered_scripts:
        marker = f'src="{script}"'
        require(index, marker, 'Spreadsheets script graph')
        positions.append(index.index(marker))
    if positions != sorted(positions):
        raise AssertionError('Spreadsheets script graph is not in dependency order')

    # Every local script/style referenced by the workspace must be present in the
    # root offline shell so a fresh controlled page can boot with the origin down.
    local_refs = re.findall(r'<script[^>]+src="([^"?#]+)', index)
    local_refs += re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"?#]+)', index)
    for ref in local_refs:
        if ref.startswith(('http://', 'https://', '//')):
            continue
        require(service_worker, f'"./apps/spreadsheets/{ref}"', 'Spreadsheets offline shell')

    # Bootstrap surface used by browser regressions and future command-isolation tests.
    for marker in (
        'new NS.WorkbookSession()',
        'NS.FileOpenController.create',
        'NS.SaveController.create',
        'NS.EditorController.create',
        'root.__inkdosSpreadsheetsS1',
    ):
        require(app, marker, 'Spreadsheets bootstrap')
    require(frame, 'NS.FrameUI=Object.freeze', 'Spreadsheets frame module')

    # WorkbookEditor is the semantic mutation/history authority. Its size alone is
    # not a reason to split it; these APIs must remain callable independently of UI.
    for api in (
        'commitValue', 'toggleFont', 'setAlignment', 'setFont', 'setFontSize',
        'toggleMerge', 'clear', 'insertRow', 'insertColumn', 'deleteRows',
        'deleteColumns', 'operation', 'resizeColumn', 'resizeRow', 'undo', 'redo',
    ):
        require(workbook_editor, api, 'WorkbookEditor semantic API')
    require(workbook_editor, 'this.history.push', 'WorkbookEditor history ownership')
    require(workbook_session, 'commitCandidate', 'Workbook transactional session')
    require(workbook_session, 'markDirty', 'Workbook transactional session')
    require(file_open, 'session.beginOperation()', 'Workbook transactional open')
    require(file_open, 'session.isCurrent(op)', 'Workbook transactional open')
    require(save_controller, 'LocalXLSX.saveCopy', 'Workbook XLSX save path')
    require(save_controller, 'FileDelivery.deliver', 'Workbook delivery path')

    # Safety envelope for XLSX ingestion remains blocking.
    for marker in (
        'maxInputBytes', 'maxEntries', 'maxInflatedBytes', 'ZIP_PATH_INVALID',
        'ZIP_CASE_COLLISION', 'XML_DTD_FORBIDDEN', 'XLSX_REQUIRED_PART_MISSING',
    ):
        require(package_validator, marker, 'Spreadsheets package safety')

    # Both codecs remain explicit format engines. Do not infer a split requirement
    # from their physical size.
    require(xlsx_engine, 'LocalXLSX', 'XLSX engine')
    require(xls_engine, 'LocalXLS', 'XLS legacy engine')

    # Current controller must still expose the editor through a stable surface;
    # later audits may move bindings without changing this behavior.
    require(editor_controller, 'get editor(){return editor}', 'Spreadsheets editor surface')

    print('Spreadsheets stability contract: OK')


if __name__ == '__main__':
    main()
