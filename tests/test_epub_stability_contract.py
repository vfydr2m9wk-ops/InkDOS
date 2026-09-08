#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f'{label}: missing {needle!r}')


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f'{label}: forbidden {needle!r}')


def main() -> None:
    index = read('apps/epub/index.html')
    app = read('apps/epub/app.js')
    frame_module = read('apps/epub/runtime/frame/frame-menu.js')
    controls = read('apps/epub/ui/reader-controls.js')
    session = read('apps/epub/session/book-session.js')
    package_reader = read('apps/epub/io/package-reader.js')

    # The EPUB bootstrap is assembled from explicit responsibility modules.
    scripts = [
        'io/package-reader.js',
        'engine/content-projector.js',
        'engine/book-model.js',
        'state/annotation-store.js',
        'state/reading-state.js',
        'runtime/frame/frame-menu.js',
        'view/reader-viewport.js',
        'view/renderer.js',
        'session/book-session.js',
        'ui/reader-controls.js',
        'ui/navigation-tools.js',
        'app.js',
    ]
    positions = []
    for script in scripts:
        require(index, f'src="{script}"', 'EPUB script graph')
        positions.append(index.index(f'src="{script}"'))
    if positions != sorted(positions):
        raise AssertionError('EPUB script graph is not in dependency order')

    for element_id in (
        'toolbar', 'fileInput', 'readerStage', 'readerSurface', 'emptyState',
        'prevBtn', 'nextBtn', 'tocBtn', 'appearanceBtn', 'pagesBtn', 'scrollBtn',
        'progressRange', 'saveBtn', 'shareBtn',
    ):
        require(index, f'id="{element_id}"', 'EPUB frame contract')

    # Bootstrap composes frame behavior; it does not implement toolbar chrome.
    require(app, 'BookSession.create()', 'EPUB bootstrap')
    require(app, 'ReaderRenderer.create()', 'EPUB bootstrap')
    require(app, 'ReaderControls.create', 'EPUB bootstrap')
    require(app, 'ReaderNavigationTools.create', 'EPUB bootstrap')
    require(app, 'globalThis.__InkEpubR4', 'EPUB stability surface')
    require(app, 'LocalAppFrame.installToolbarRail(E.toolbar)', 'EPUB frame composition')
    forbid(app, 'function installToolbarRail', 'EPUB bootstrap isolation')
    forbid(app, "document.createElement('style')", 'EPUB bootstrap isolation')
    require(frame_module, 'function installToolbarRail(target)', 'EPUB frame authority')
    require(frame_module, 'NS.LocalAppFrame={create,configureOptionalHome,installToolbarRail}', 'EPUB frame authority')

    # Reading operations remain semantic APIs rather than toolbar-only behavior.
    for api in ('goPage', 'setFlow', 'setFont', 'setFontStyle', 'goLocator', 'goPath', 'prepareExport'):
        require(controls, api, 'EPUB reader API')
    require(session, 'loadCandidate', 'EPUB transactional session')
    require(session, 'isCurrent(candidate)', 'EPUB transactional session')
    require(session, 'commit(candidate)', 'EPUB transactional session')
    require(session, 'prepareExport', 'EPUB transactional session')

    # Package ingestion keeps the existing local-first safety envelope.
    for marker in ('DEFAULT_BUDGETS', 'unsafe-path', 'duplicate-path', 'compression-ratio', 'epub-mimetype'):
        require(package_reader, marker, 'EPUB package safety')

    print('EPUB stability contract: OK')


if __name__ == '__main__':
    main()
