#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"


def wait_port(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_port(PORT)
        with sync_playwright() as pw:
            launch_args = {"headless": True}
            chromium_path = os.environ.get("CHROMIUM_PATH")
            if chromium_path:
                launch_args["executable_path"] = chromium_path
            browser = pw.chromium.launch(**launch_args)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + "/apps/documents/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2Documents?.DocumentsApp?.d1")
            result = page.evaluate(
                """async () => {
                  const NS = globalThis.InkDOS2Documents;
                  const app = NS.DocumentsApp;
                  await app.newDocument();
                  const host = document.getElementById('pagesHost');
                  const pageEl = host.querySelector('.doc-page');
                  const content = pageEl.querySelector('.page-content');
                  content.innerHTML = `
                    <p>First paragraph</p>
                    <p data-page-break-before="1" data-d1-formatting="1">
                      <span style="color:#123456;background-color:#ffee33;text-decoration:line-through">Strike color highlight</span>
                      <span style="vertical-align:sub;font-size:9pt"> sub</span>
                      <span style="vertical-align:super;font-size:9pt"> super</span>
                    </p>`;
                  pageEl._pageSpec = NS.PageSpec.normalize({
                    ...pageEl._pageSpec,
                    widthPx: 1122.519685,
                    heightPx: 793.700787,
                    marginTopPx: 56.692913,
                    marginRightPx: 75.590551,
                    marginBottomPx: 56.692913,
                    marginLeftPx: 75.590551,
                    contentWidthPx: 971.338583,
                    contentHeightPx: 680.314961,
                    orientation: 'landscape',
                    headerText: 'D1 Header',
                    footerText: 'D1 Footer',
                    pageNumber: true,
                  });
                  host.dataset.d1LayoutDirty = '1';
                  host.dataset.d1HeaderFooterDirty = '1';

                  const saved = await NS.DocxWriter.save(host, 'Roundtrip.docx', null, null);
                  const bytes = new Uint8Array(await saved.blob.arrayBuffer());
                  const zip = await JSZip.loadAsync(bytes);
                  const text = async path => zip.file(path) ? zip.file(path).async('string') : '';
                  const docXml = await text('word/document.xml');
                  const relsXml = await text('word/_rels/document.xml.rels');
                  const headerXml = await text('word/header-inkdos-d1.xml');
                  const footerXml = await text('word/footer-inkdos-d1.xml');
                  const typesXml = await text('[Content_Types].xml');
                  const parseXml = value => new DOMParser().parseFromString(value, 'application/xml');
                  const doc = parseXml(docXml);
                  const byLocal = (root, name) => [...root.getElementsByTagNameNS('*', name)];
                  const attr = (el, local) => {
                    if (!el) return '';
                    for (const a of [...el.attributes]) if (a.localName === local) return a.value;
                    return '';
                  };
                  const pgSz = byLocal(doc, 'pgSz')[0];
                  const pgMar = byLocal(doc, 'pgMar')[0];
                  const vertValues = byLocal(doc, 'vertAlign').map(x => attr(x, 'val'));
                  const shading = byLocal(doc, 'shd').map(x => attr(x, 'fill'));
                  const colors = byLocal(doc, 'color').map(x => attr(x, 'val'));

                  const parsed = await NS.DocxParser.parse(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
                  const parsedHtml = (parsed.blocks || []).map(x => x.html || '').join('\n');
                  const file = new File([bytes], 'Roundtrip.docx', {type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'});
                  const reopened = await app.open(file, {authorized:true});
                  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                  const reopenedPage = host.querySelector('.doc-page');
                  const reopenedText = host.querySelector('.page-content')?.innerText || '';
                  const reopenedSpec = reopenedPage?._pageSpec || {};
                  const pageNumber = host.querySelector('.d1-page-number')?.textContent || '';
                  return {
                    zipNames: Object.keys(zip.files),
                    ooxml: {
                      orient: attr(pgSz, 'orient'), width: Number(attr(pgSz, 'w')), height: Number(attr(pgSz, 'h')),
                      top: Number(attr(pgMar, 'top')), right: Number(attr(pgMar, 'right')), bottom: Number(attr(pgMar, 'bottom')), left: Number(attr(pgMar, 'left')),
                      pageBreak: byLocal(doc, 'pageBreakBefore').length,
                      strike: byLocal(doc, 'strike').length,
                      vertValues, shading, colors,
                      headerXml, footerXml, relsXml, typesXml,
                    },
                    parsed: {
                      orientation: parsed.pageSpec?.orientation || '',
                      headerText: parsed.pageSpec?.headerText || '',
                      footerText: parsed.pageSpec?.footerText || '',
                      pageNumber: !!parsed.pageSpec?.pageNumber,
                      pageBreak: (parsed.blocks || []).some(x => !!x.hardPageBreakBefore),
                      html: parsedHtml,
                    },
                    reopened: {
                      ok: !!reopened,
                      orientation: reopenedSpec.orientation || '',
                      headerText: reopenedSpec.headerText || '',
                      footerText: reopenedSpec.footerText || '',
                      pageNumberEnabled: !!reopenedSpec.pageNumber,
                      pageNumber,
                      text: reopenedText,
                      pages: host.querySelectorAll('.doc-page').length,
                    },
                  };
                }"""
            )
            browser.close()

        ooxml = result["ooxml"]
        assert ooxml["orient"] == "landscape", result
        assert ooxml["width"] > ooxml["height"] > 0, result
        assert all(ooxml[k] > 0 for k in ("top", "right", "bottom", "left")), result
        assert ooxml["pageBreak"] >= 1, result
        assert ooxml["strike"] >= 1, result
        assert "subscript" in ooxml["vertValues"] and "superscript" in ooxml["vertValues"], result
        assert "FFEE33" in [x.upper() for x in ooxml["shading"]], result
        assert "123456" in [x.upper() for x in ooxml["colors"]], result
        assert "D1 Header" in ooxml["headerXml"], result
        assert "D1 Footer" in ooxml["footerXml"] and "PAGE" in ooxml["footerXml"], result
        assert "header-inkdos-d1.xml" in ooxml["relsXml"] and "footer-inkdos-d1.xml" in ooxml["relsXml"], result
        assert "/word/header-inkdos-d1.xml" in ooxml["typesXml"], result
        assert "/word/footer-inkdos-d1.xml" in ooxml["typesXml"], result

        parsed = result["parsed"]
        assert parsed["orientation"] == "landscape", result
        assert parsed["headerText"] == "D1 Header", result
        assert parsed["footerText"] == "D1 Footer", result
        assert parsed["pageNumber"] is True, result
        assert parsed["pageBreak"] is True, result
        assert "line-through" in parsed["html"], result
        assert "background-color" in parsed["html"], result
        assert "vertical-align:sub" in parsed["html"] and "vertical-align:super" in parsed["html"], result

        reopened = result["reopened"]
        assert reopened["ok"] is True, result
        assert reopened["orientation"] == "landscape", result
        assert reopened["headerText"] == "D1 Header", result
        assert reopened["footerText"] == "D1 Footer", result
        assert reopened["pageNumberEnabled"] is True, result
        assert reopened["pageNumber"] == "1", result
        assert "First paragraph" in reopened["text"] and "Strike color highlight" in reopened["text"], result
        assert reopened["pages"] >= 2, result
        print("DOC-D1 browser save/OOXML/reopen roundtrip passed.")
        print(json.dumps({"pages": reopened["pages"], "orientation": reopened["orientation"]}, sort_keys=True))
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
