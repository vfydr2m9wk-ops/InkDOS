#!/usr/bin/env python3
"""Fail the release if retired PDF/runtime mechanisms return."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PDF_HTML = ROOT / 'apps' / 'pdf' / 'index.html'
PDF_JS = ROOT / 'apps' / 'pdf' / 'app.js'
PDF_CSS = ROOT / 'apps' / 'pdf' / 'styles.css'
SERVICE_WORKER = ROOT / 'service-worker.js'
VENDOR = ROOT / 'shared' / 'vendor' / 'pdfjs'

errors: list[str] = []


def reject(text: str, path: Path, tokens: tuple[str, ...]) -> None:
    lowered = text.lower()
    for token in tokens:
        if token.lower() in lowered:
            errors.append(f'{path.relative_to(ROOT)} contains retired token {token!r}')


def require(text: str, path: Path, tokens: tuple[str, ...]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f'{path.relative_to(ROOT)} is missing required architecture marker {token!r}')


html = PDF_HTML.read_text(encoding='utf-8')
javascript = PDF_JS.read_text(encoding='utf-8')
css = PDF_CSS.read_text(encoding='utf-8')
service_worker = SERVICE_WORKER.read_text(encoding='utf-8')

reject(html, PDF_HTML, ('<object', '<embed', '<iframe', 'type="module"', '.mjs', 'nativeMount', 'nativeStatus'))
reject(javascript, PDF_JS, (
    "document.createElement('object')", 'document.createElement("object")',
    "document.createElement('embed')", 'document.createElement("embed")',
    "document.createElement('iframe')", 'document.createElement("iframe")',
    '#page=', 'pdf.min.mjs', 'pdf.worker.min.mjs', 'state.embedUrl',
    '/Type\\s*\\/Pages', 'nativeMount', 'nativeStatus',
))
reject(css, PDF_CSS, ('native-pdf-object', 'native-pdf-embed', 'native-mount', 'native-status'))
reject(service_worker, SERVICE_WORKER, ('pdf.min.mjs', 'pdf.worker.min.mjs'))

require(html, PDF_HTML, (
    '../../shared/vendor/pdfjs/pdf.min.js?v=3.11.174',
    'id="pdfPages"', 'id="pdfStatus"', 'id="saveModifiedPdfBtn"',
))
require(javascript, PDF_JS, (
    "pdfjsLib.GlobalWorkerOptions.workerSrc = '../../shared/vendor/pdfjs/pdf.worker.min.js'",
    'pdfjsLib.getDocument(', 'pdfjsLib.renderTextLayer(',
    'new pdfjsLib.AnnotationLayer(', 'state.doc.saveDocument()',
    'CACHE_RADIUS=2', 'MAX_CANVAS_PIXELS=', 'record.canvas.width=0',
))
require(service_worker, SERVICE_WORKER, (
    "'./shared/vendor/pdfjs/pdf.min.js'",
    "'./shared/vendor/pdfjs/pdf.worker.min.js'",
))

expected_vendor = {'pdf.min.js', 'pdf.worker.min.js', 'LICENSE-PDFJS.txt'}
actual_vendor = {path.name for path in VENDOR.iterdir() if path.is_file()}
if actual_vendor != expected_vendor:
    errors.append(f'PDF.js vendor inventory is {sorted(actual_vendor)!r}, expected {sorted(expected_vendor)!r}')

stale_assets = sorted(
    path.relative_to(ROOT).as_posix()
    for path in ROOT.rglob('*')
    if path.is_file() and path.suffix.lower() == '.mjs'
)
if stale_assets:
    errors.append('ES-module assets are forbidden in the direct-file release: ' + ', '.join(stale_assets))

if errors:
    print('\n'.join('ERROR: ' + error for error in errors))
    raise SystemExit(1)

print('OK: no retired PDF viewer, embed, fragment-navigation, or local ES-module runtime remains.')
