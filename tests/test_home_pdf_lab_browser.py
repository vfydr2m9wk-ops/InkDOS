#!/usr/bin/env python3
"""PDF tools (beta, web only): OCR, visual signature, digital signature and signature check.

Everything is built inside the page (no fixture files): a "scanned" PDF made from a canvas
picture of text, and a throw-away self-signed RSA certificate (.p12) made with forge. The OCR
result must be searchable, two successive digital signatures must both verify, a stamped picture
must be added, and changing one signed byte must be reported.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8794

SCRIPT = r"""async () => {
  // a scanned page: text drawn on a canvas, embedded as a picture
  const c = document.createElement('canvas'); c.width = 1240; c.height = 1754;
  const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.fillStyle = '#000';
  g.font = '64px serif'; g.fillText('Relatorio anual de vendas', 120, 300); g.fillText('Contrato assinado em Lisboa', 120, 420);
  const png = Uint8Array.from(atob(c.toDataURL('image/png').split(',')[1]), ch => ch.charCodeAt(0));
  const d = await PDFLib.PDFDocument.create(), img = await d.embedPng(png), p = d.addPage([595, 842]);
  p.drawImage(img, { x: 0, y: 0, width: 595, height: 842 });
  const scanned = await d.save();

  const ocr = await InkDOSPdfLabOcr.ocrPdf(scanned, { languages: 'por' });
  const pdf = await pdfjsLib.getDocument({ data: ocr.bytes.slice(), isEvalSupported: false }).promise;
  const text = (await (await pdf.getPage(1)).getTextContent()).items.map(i => i.str).join(' ');

  // throw-away certificate
  const keys = forge.pki.rsa.generateKeyPair(1024), cert = forge.pki.createCertificate();
  cert.publicKey = keys.publicKey; cert.serialNumber = '01'; cert.validity.notBefore = new Date(Date.now() - 864e5); cert.validity.notAfter = new Date(Date.now() + 864e5);
  const attrs = [{ name: 'commonName', value: 'Teste Lab' }]; cert.setSubject(attrs); cert.setIssuer(attrs); cert.sign(keys.privateKey, forge.md.sha256.create());
  const p12der = forge.asn1.toDer(forge.pkcs12.toPkcs12Asn1(keys.privateKey, [cert], 'senha', { algorithm: '3des' })).getBytes();
  const p12 = Uint8Array.from(p12der, ch => ch.charCodeAt(0));

  const once = await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12, password: 'senha', reason: 'Aprovação' });
  const twice = await InkDOSPdfLabSign.signPdf(once.bytes, { p12, password: 'senha', reason: 'Revisão' });
  const checks = await InkDOSPdfLabSign.checkPdf(twice.bytes);
  const tampered = twice.bytes.slice(); tampered[200] ^= 1;
  const broken = await InkDOSPdfLabSign.checkPdf(tampered);
  let wrongPassword = '';
  try { await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12, password: 'x' }); } catch (e) { wrongPassword = e.message; }
  const locked = await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12, password: 'senha', visible: { position: 'bottom-right' }, lock: true, labels: { signedBy: 'Assinado por', date: 'Data' } });
  const lockedCheck = await InkDOSPdfLabSign.checkPdf(locked.bytes);
  let resign = ''; try { await InkDOSPdfLabSign.signPdf(locked.bytes, { p12, password: 'senha' }); } catch (e) { resign = e.message; }
  const appended = new Uint8Array([...locked.bytes, ...new TextEncoder().encode('\n% change\n')]);
  const lockedChanged = (await InkDOSPdfLabSign.checkPdf(appended)).map(r => r.ok);
  const stampPdf = await pdfjsLib.getDocument({ data: locked.bytes.slice(), isEvalSupported: false }).promise;
  const annots = await (await stampPdf.getPage(1)).getAnnotations();
  return { locked: lockedCheck.map(r => [r.ok, r.locked]), resign, lockedChanged, widget: annots.filter(a => a.fieldType === 'Sig').map(a => a.rect.map(Math.round)),
    words: ocr.words, text, checks: checks.map(r => [r.ok, r.coversWholeFile, r.signer, r.reason]), broken: broken.map(r => r.ok), wrongPassword };
}"""


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(('127.0.0.1', PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError('Local test server did not start')


def main() -> None:
    server = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, os.environ.get('BROWSER', 'chromium')).launch(headless=True)
            page = browser.new_context(service_workers='block').new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{PORT}/labs/pdf/index.html', wait_until='load')
            page.wait_for_function('() => !!globalThis.InkDOSPdfLabOcr && !!globalThis.InkDOSPdfLabSign')
            got = page.evaluate(SCRIPT)
            assert got['words'] >= 6, got
            assert 'vendas' in got['text'].lower() and 'contrato' in got['text'].lower(), got['text']
            assert got['checks'] == [[True, False, 'Teste Lab', 'Aprovação'], [True, True, 'Teste Lab', 'Revisão']], got['checks']
            assert got['broken'] == [False, False], got['broken']
            assert 'password' in got['wrongPassword'].lower(), got['wrongPassword']
            assert got['locked'] == [[True, True]], got['locked']
            assert 'locked' in got['resign'].lower(), got['resign']
            assert got['lockedChanged'] == [False], got['lockedChanged']
            assert len(got['widget']) == 1 and got['widget'][0][2] - got['widget'][0][0] == 250, got['widget']
            # the page itself loads without errors and the Home link exists on the web edition
            home = (ROOT / 'index.html').read_text(encoding='utf-8')
            assert 'href="./labs/pdf/index.html"' in home and 'class="web-only"' in home
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('PDF tools (beta): OCR, digital signatures and checks passed')


if __name__ == '__main__':
    main()
