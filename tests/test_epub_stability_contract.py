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


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f'{label}: forbidden {needle!r}')


def main() -> None:
    index = read('apps/epub/index.html')
    app = read('apps/epub/app.js')
    frame_module = read('apps/epub/runtime/frame/frame-menu.js')
    controls = read('apps/epub/ui/reader-controls.js')
    bindings = read('apps/epub/ui/reader-bindings.js')
    navigation = read('apps/epub/ui/navigation-tools.js')
    session = read('apps/epub/session/book-session.js')
    package_reader = read('apps/epub/io/package-reader.js')
    service_worker = read('service-worker.js')

    # The EPUB bootstrap is assembled from explicit responsibility modules.
    scripts = [
        'io/package-reader.js',
        'engine/content-projector.js',
        'engine/book-model.js',
        'engine/navigation-index.js',
        'state/annotation-store.js',
        'engine/annotations.js',
        'io/epub-writer.js',
        'io/file-delivery.js',
        'state/reading-state.js',
        'state/appearance.js',
        'runtime/frame/frame-menu.js',
        'view/reader-viewport.js',
        'view/renderer.js',
        'session/book-session.js',
        'ui/reader-controls.js',
        'ui/reader-bindings.js',
        'ui/navigation-tools.js',
        'app.js',
    ]
    positions = []
    for script in scripts:
        require(index, f'src="{script}"', 'EPUB script graph')
        positions.append(index.index(f'src="{script}"'))
    if positions != sorted(positions):
        raise AssertionError('EPUB script graph is not in dependency order')

    # Every local runtime dependency referenced by the EPUB document must be
    # explicitly known to the offline shell. A cached index without one of its
    # scripts/styles is not a valid offline boot.
    local_refs = re.findall(r'<script[^>]+src="([^"?#]+)', index)
    local_refs += re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"?#]+)', index)
    for ref in local_refs:
        if ref.startswith(('http://', 'https://', '//')):
            continue
        require(service_worker, f'"./apps/epub/{ref}"', 'EPUB offline shell')
    require(service_worker, 'inkdos-v2.0.12-stability-epub-seq89', 'EPUB offline cache rotation')

    for element_id in (
        'toolbar', 'fileInput', 'readerStage', 'readerSurface', 'emptyState',
        'prevBtn', 'nextBtn', 'tocBtn', 'appearanceBtn', 'pagesBtn', 'scrollBtn',
        'progressRange', 'saveBtn', 'shareBtn',
    ):
        require(index, f'id="{element_id}"', 'EPUB frame contract')

    # Bootstrap composes responsibilities instead of implementing frame or bindings.
    require(app, 'BookSession.create()', 'EPUB bootstrap')
    require(app, 'ReaderRenderer.create()', 'EPUB bootstrap')
    require(app, 'ReaderControls.create', 'EPUB bootstrap')
    require(app, 'ReaderBindings.create', 'EPUB bootstrap')
    require(app, 'ReaderNavigationTools.create', 'EPUB bootstrap')
    require(app, "bookmarkBtn:$('bookmarkBtn')", 'EPUB optional control composition')
    require(app, "searchBtn:$('searchBtn')", 'EPUB optional control composition')
    require(app, 'navigation:navigation.api', 'EPUB binding composition')
    require(app, 'globalThis.__InkEpubR4', 'EPUB stability surface')
    require(app, 'LocalAppFrame.installToolbarRail(E.toolbar)', 'EPUB frame composition')
    forbid(app, 'function installToolbarRail', 'EPUB bootstrap isolation')
    forbid(app, "document.createElement('style')", 'EPUB bootstrap isolation')
    require(frame_module, 'function installToolbarRail(target)', 'EPUB frame authority')
    require(frame_module, 'NS.LocalAppFrame={create,configureOptionalHome,installToolbarRail}', 'EPUB frame authority')

    # ReaderControls owns reader behavior; ReaderBindings owns toolbar/control wiring.
    forbid(controls, 'addEventListener', 'EPUB reader semantic isolation')
    for api in ('openNavigationSheet', 'closeNavigationSheet', 'toggleNavigationSheet'):
        require(controls, api, 'EPUB navigation sheet API')
    require(bindings, 'addEventListener', 'EPUB reader binding authority')
    require(bindings, "navigation.showTab('contents')", 'EPUB navigation binding')
    require(bindings, "if(E.bookmarkBtn)E.bookmarkBtn.addEventListener('click',()=>navigation.toggleBookmark())", 'EPUB optional bookmark binding')
    require(bindings, "if(E.searchBtn)E.searchBtn.addEventListener('click',()=>navigation.openNavigation('search'))", 'EPUB optional search binding')
    require(bindings, 'NS.ReaderBindings=Object.freeze({create})', 'EPUB reader binding authority')
    for api in (
        'goPage', 'setFlow', 'setFont', 'setFontStyle', 'setTheme', 'goLocator',
        'goPath', 'openFile', 'saveCopy', 'shareCopy', 'prepareExport',
    ):
        require(controls, api, 'EPUB reader API')

    # Navigation features invoke semantic reader APIs, never toolbar controls.
    require(navigation, 'reader.openNavigationSheet()', 'EPUB navigation semantic routing')
    forbid(navigation, 'tocBtn.click()', 'EPUB navigation control coupling')
    forbid(navigation, 'E.tocBtn.addEventListener', 'EPUB navigation control binding')
    forbid(navigation, 'ui.searchBtn.addEventListener', 'EPUB search toolbar coupling')
    forbid(navigation, 'ui.bookmarkBtn.addEventListener', 'EPUB bookmark toolbar coupling')
    require(navigation, 'toggleBookmark', 'EPUB bookmark semantic API')
    require(navigation, 'openNavigation', 'EPUB search/navigation semantic API')

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
