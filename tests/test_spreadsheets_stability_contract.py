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


def require_any(text: str, needles: tuple[str, ...], label: str) -> None:
    if not any(needle in text for needle in needles):
        raise AssertionError(f'{label}: missing one of {needles!r}')


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f'{label}: forbidden {needle!r}')


def main() -> None:
    index = read('apps/spreadsheets/index.html')
    app = read('apps/spreadsheets/app.js')
    frame = read('apps/spreadsheets/runtime/frame/frame-menu.js')
    chrome_controller = read('apps/spreadsheets/ui/chrome-controller.js')
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

    local_refs = re.findall(r'<script[^>]+src="([^"?#]+)', index)
    local_refs += re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"?#]+)', index)
    for ref in local_refs:
        if ref.startswith(('http://', 'https://', '//')):
            continue
        require(service_worker, f'"./apps/spreadsheets/{ref}"', 'Spreadsheets offline shell')

    for marker in (
        'new NS.WorkbookSession()',
        'NS.FileOpenController.create',
        'NS.SaveController.create',
        'NS.EditorController.create',
        'chrome.bindEditorControls(editorController.commands)',
        'root.__inkdosSpreadsheetsS1',
    ):
        require(app, marker, 'Spreadsheets bootstrap')

    # App bootstrap composes frame behavior; the frame module owns toolbar rail.
    require(frame, 'function installToolbarRail(target)', 'Spreadsheets frame authority')
    require(frame, 'installToolbarRail', 'Spreadsheets frame authority')
    require(app, "NS.FrameUI.installToolbarRail(document.getElementById('formatbar'))", 'Spreadsheets frame composition')
    forbid(app, 'function installToolbarRail', 'Spreadsheets bootstrap frame isolation')
    forbid(app, 'inkdosToolbarRailStyle', 'Spreadsheets bootstrap frame isolation')
    forbid(app, "document.createElement('style')", 'Spreadsheets bootstrap frame isolation')

    # EditorController owns semantic orchestration and a stable command facade;
    # ChromeController owns toolbar DOM binding/projection. Formatting commands may
    # use the guarded registration path so CSV/TSV can require explicit XLSX promotion.
    require_any(editor_controller, ("register('format.bold'", "registerGuarded('format.bold'"), 'Spreadsheets bold command facade')
    require_any(editor_controller, ("register('format.italic'", "registerGuarded('format.italic'"), 'Spreadsheets italic command facade')
    for marker in (
        "register('edit.undo'",
        "register('edit.redo'",
        "register('file.save'",
        "register('file.open'",
        'SPREADSHEET_COMMAND_NOT_REGISTERED',
        'commands,get selection',
    ):
        require(editor_controller, marker, 'Spreadsheets command facade')
    require(editor_controller, 'chrome.syncEditorToolbar', 'Spreadsheets toolbar projection routing')
    forbid(editor_controller, "$('boldBtn').onclick", 'Spreadsheets toolbar binding isolation')
    forbid(editor_controller, "$('undoBtn').onclick", 'Spreadsheets toolbar binding isolation')
    forbid(editor_controller, "$('redoBtn').onclick", 'Spreadsheets toolbar binding isolation')
    require(chrome_controller, 'function syncEditorToolbar', 'Spreadsheets toolbar projection authority')
    require(chrome_controller, 'function bindEditorControls(commands)', 'Spreadsheets toolbar binding authority')
    require(chrome_controller, "commands.execute('format.bold')", 'Spreadsheets toolbar command routing')
    require(chrome_controller, "commands.execute('edit.undo')", 'Spreadsheets toolbar command routing')
    require(chrome_controller, "commands.execute('edit.redo')", 'Spreadsheets toolbar command routing')
    forbid(chrome_controller, "editor.toggleFont('bold')", 'Spreadsheets chrome semantic isolation')

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

    for marker in (
        'maxInputBytes', 'maxEntries', 'maxInflatedBytes', 'ZIP_PATH_INVALID',
        'ZIP_CASE_COLLISION', 'XML_DTD_FORBIDDEN', 'XLSX_REQUIRED_PART_MISSING',
    ):
        require(package_validator, marker, 'Spreadsheets package safety')

    require(xlsx_engine, 'LocalXLSX', 'XLSX engine')
    require(xls_engine, 'LocalXLS', 'XLS legacy engine')

    require(editor_controller, 'get editor(){return editor}', 'Spreadsheets editor surface')

    print('Spreadsheets stability contract: OK')


if __name__ == '__main__':
    main()
