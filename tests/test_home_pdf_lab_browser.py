#!/usr/bin/env python3
"""PDF tools (beta, web only): OCR, visual signature, digital signature and signature check.

Everything is built inside the page (no fixture files): a "scanned" PDF made from a canvas
picture of text, and a throw-away self-signed RSA certificate (.p12) made with forge. The OCR
result must be searchable, two successive digital signatures must both verify, a stamped picture
must be added, and changing one signed byte must be reported. Signatures are PAdES
(ETSI.CAdES.detached); expired or weak certificates are refused, and a byte range that leaves
out more than the signature itself is reported as invalid. The bundled ICP-Brasil list loads, a
chain is trusted only through a listed root (a test root is swapped in), the AD-RB policy is
declared on request, and the ITI validator is opened only from the warning dialog, by the user.
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
  const keys = forge.pki.rsa.generateKeyPair(2048), cert = forge.pki.createCertificate();
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
  // certificates that must not sign: expired, and a 1024-bit key
  const p12Of = (key, c) => Uint8Array.from(forge.asn1.toDer(forge.pkcs12.toPkcs12Asn1(key, [c], 'senha', { algorithm: '3des' })).getBytes(), ch => ch.charCodeAt(0));
  const old = forge.pki.createCertificate(); old.publicKey = keys.publicKey; old.serialNumber = '02';
  old.validity.notBefore = new Date(Date.now() - 3e10); old.validity.notAfter = new Date(Date.now() - 864e5); old.setSubject(attrs); old.setIssuer(attrs); old.sign(keys.privateKey, forge.md.sha256.create());
  let expired = ''; try { await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12: p12Of(keys.privateKey, old), password: 'senha' }); } catch (e) { expired = e.message; }
  const small = forge.pki.rsa.generateKeyPair(1024), weakCert = forge.pki.createCertificate(); weakCert.publicKey = small.publicKey; weakCert.serialNumber = '03';
  weakCert.validity.notBefore = cert.validity.notBefore; weakCert.validity.notAfter = cert.validity.notAfter; weakCert.setSubject(attrs); weakCert.setIssuer(attrs); weakCert.sign(small.privateKey, forge.md.sha256.create());
  let weak = ''; try { await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12: p12Of(small.privateKey, weakCert), password: 'senha' }); } catch (e) { weak = e.message; }
  // widen the unsigned gap of the first signature by ten bytes (same text length)
  const raw = new TextDecoder('latin1').decode(once.bytes), at = raw.indexOf('/ByteRange [') + 11, close = raw.indexOf(']', at) + 1;
  const [r0, r1, r2, r3] = raw.slice(at + 1, close - 1).trim().split(/\s+/).map(Number);
  const widened = once.bytes.slice(); widened.set(new TextEncoder().encode(('[' + [r0, r1 - 10, r2, r3].join(' ') + ']').padEnd(close - at, ' ')), at);
  const gap = (await InkDOSPdfLabSign.checkPdf(widened)).map(r => [r.ok, r.problems.join(' ')]);
  // trust: the bundled ICP-Brasil list does not trust the self-signed test certificate
  const bundled = InkDOSPdfLabSign._test.trustPool(), bundle = [bundled.name, bundled.anchors.length, bundled.intermediates.length, globalThis.InkDOSPdfLabTrust.intermediates.length];
  const realTrust = checks.map(r => r.trust);
  // every bundled ICP-Brasil CA that is valid today builds a trusted path with WebCrypto (real keys and algorithms)
  const all = [...bundled.intermediates, ...bundled.anchors], today = new Date();
  const current = bundled.intermediates.filter(c => today >= c.notBefore && today <= c.notAfter);
  const realPaths = [];
  for (const c of current) { const r = await InkDOSPdfLabSign._test.buildChain(c, all, today); realPaths.push(r.trusted ? 'trusted' : r.status); }
  // Ed448 and post-quantum hierarchies are reported as unsupported where WebCrypto lacks them, never trusted
  const realChains = [current.length, realPaths.filter(x => x === 'trusted').length, realPaths.filter(x => x !== 'trusted' && x !== 'unsupported')];
  // a test root swapped in as the only anchor; the .p12 carries just the end-entity certificate,
  // so the path must be completed from the trust list
  const caKeys = forge.pki.rsa.generateKeyPair(2048), eeKeys = forge.pki.rsa.generateKeyPair(2048);
  const mk = (pub, serial, subj, iss, signKey, isCa) => { const c = forge.pki.createCertificate(); c.publicKey = pub; c.serialNumber = serial;
    c.validity.notBefore = new Date(Date.now() - 864e5); c.validity.notAfter = new Date(Date.now() + 864e5 * 30); c.setSubject([{ name: 'commonName', value: subj }]); c.setIssuer([{ name: 'commonName', value: iss }]);
    c.setExtensions(isCa ? [{ name: 'basicConstraints', cA: true }, { name: 'keyUsage', keyCertSign: true, cRLSign: true }] : [{ name: 'basicConstraints', cA: false }, { name: 'keyUsage', digitalSignature: true, nonRepudiation: true }]);
    c.sign(signKey, forge.md.sha256.create()); return c; };
  const caCert = mk(caKeys.publicKey, '0a', 'Raiz Teste', 'Raiz Teste', caKeys.privateKey, true), eeCert = mk(eeKeys.publicKey, '0b', 'Fulano Teste', 'Raiz Teste', caKeys.privateKey, false);
  const realList = globalThis.InkDOSPdfLabTrust;
  globalThis.InkDOSPdfLabTrust = { name: 'Lista de teste', anchors: [{ der: btoa(forge.asn1.toDer(forge.pki.certificateToAsn1(caCert)).getBytes()) }], intermediates: [] };
  InkDOSPdfLabSign._test.resetTrust();
  const chained = await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12: p12Of(eeKeys.privateKey, eeCert), password: 'senha', policy: 'AD-RB' });
  const trusted = (await InkDOSPdfLabSign.checkPdf(chained.bytes)).map(r => [r.ok, r.trust, r.trustAnchor, r.chain, r.policy, r.notes.includes('revocation-not-checked')]);
  const selfSignedUnderTestList = (await InkDOSPdfLabSign.checkPdf(once.bytes)).map(r => r.trust);
  // a certificate that expired before today is not trusted on the strength of a signing time the
  // signer chose (no checked timestamp), even when that time falls inside its validity
  const oldRootKeys = forge.pki.rsa.generateKeyPair(2048), oldRoot = forge.pki.createCertificate(); oldRoot.publicKey = oldRootKeys.publicKey; oldRoot.serialNumber = '0e';
  oldRoot.validity.notBefore = new Date(Date.now() - 864e5 * 90); oldRoot.validity.notAfter = new Date(Date.now() + 864e5 * 90);
  oldRoot.setSubject([{ name: 'commonName', value: 'Raiz Antiga' }]); oldRoot.setIssuer([{ name: 'commonName', value: 'Raiz Antiga' }]);
  oldRoot.setExtensions([{ name: 'basicConstraints', cA: true }, { name: 'keyUsage', keyCertSign: true, cRLSign: true }]); oldRoot.sign(oldRootKeys.privateKey, forge.md.sha256.create());
  globalThis.InkDOSPdfLabTrust.anchors.push({ der: btoa(forge.asn1.toDer(forge.pki.certificateToAsn1(oldRoot)).getBytes()) }); InkDOSPdfLabSign._test.resetTrust();
  const oldKeys = forge.pki.rsa.generateKeyPair(2048), lapsed = forge.pki.createCertificate(); lapsed.publicKey = oldKeys.publicKey; lapsed.serialNumber = '0c';
  lapsed.validity.notBefore = new Date(Date.now() - 864e5 * 60); lapsed.validity.notAfter = new Date(Date.now() - 864e5 * 30);
  lapsed.setSubject([{ name: 'commonName', value: 'Fulano Vencido' }]); lapsed.setIssuer([{ name: 'commonName', value: 'Raiz Antiga' }]);
  lapsed.setExtensions([{ name: 'basicConstraints', cA: false }, { name: 'keyUsage', digitalSignature: true, nonRepudiation: true }]); lapsed.sign(oldRootKeys.privateKey, forge.md.sha256.create());
  const backdated = await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12: p12Of(oldKeys.privateKey, lapsed), password: 'senha', now: new Date(Date.now() - 864e5 * 45) });
  const backdatedCheck = (await InkDOSPdfLabSign.checkPdf(backdated.bytes)).map(r => [r.trust, r.notes.includes('not-valid-now')]);
  // a CA certificate is not accepted as the signer (the new signature's own check refuses it)
  const caSigner = forge.pki.createCertificate(), caSignerKeys = forge.pki.rsa.generateKeyPair(2048); caSigner.publicKey = caSignerKeys.publicKey; caSigner.serialNumber = '0d';
  caSigner.validity.notBefore = new Date(Date.now() - 864e5); caSigner.validity.notAfter = new Date(Date.now() + 864e5 * 30);
  caSigner.setSubject([{ name: 'commonName', value: 'AC Intermediaria' }]); caSigner.setIssuer([{ name: 'commonName', value: 'Raiz Teste' }]);
  caSigner.setExtensions([{ name: 'basicConstraints', cA: true }]); caSigner.sign(caKeys.privateKey, forge.md.sha256.create());
  let caSignedCheck = ''; try { await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12: p12Of(caSignerKeys.privateKey, caSigner), password: 'senha' }); } catch (e) { caSignedCheck = e.message; }
  globalThis.InkDOSPdfLabTrust = realList; InkDOSPdfLabSign._test.resetTrust();
  let unknownPolicy = ''; try { await InkDOSPdfLabSign.signPdf(ocr.bytes, { p12, password: 'senha', policy: 'XYZ' }); } catch (e) { unknownPolicy = e.message; }
  const appended = new Uint8Array([...locked.bytes, ...new TextEncoder().encode('\n% change\n')]);
  const lockedChanged = (await InkDOSPdfLabSign.checkPdf(appended)).map(r => r.ok);
  const stampPdf = await pdfjsLib.getDocument({ data: locked.bytes.slice(), isEvalSupported: false }).promise;
  const annots = await (await stampPdf.getPage(1)).getAnnotations();
  return { locked: lockedCheck.map(r => [r.ok, r.locked]), resign, lockedChanged, widget: annots.filter(a => a.fieldType === 'Sig').map(a => a.rect.map(Math.round)),
    words: ocr.words, text, checks: checks.map(r => [r.ok, r.coversWholeFile, r.signer, r.reason]), broken: broken.map(r => r.ok), wrongPassword,
    pades: checks.map(r => [r.subFilter, r.chainStatus, r.notes.includes('no-timestamp'), r.notes.includes('no-signing-certificate')]), expired, weak, gap, bundle, realTrust, trusted, selfSignedUnderTestList, unknownPolicy, realChains, backdatedCheck, caSignedCheck,
    twice: btoa(Array.from(twice.bytes, ch => String.fromCharCode(ch)).join('')) };
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
            assert got['pades'] == [['ETSI.CAdES.detached', 'root', True, False]] * 2, got['pades']
            assert 'expired' in got['expired'].lower(), got['expired']
            assert '2048' in got['weak'], got['weak']
            assert got['gap'][0][0] is False and 'byte range' in got['gap'][0][1].lower(), got['gap']
            assert got['bundle'][0] == 'ICP-Brasil' and got['bundle'][1] == 4 and got['bundle'][2] == got['bundle'][3] > 100, got['bundle']
            assert got['realTrust'] == [None, None], got['realTrust']
            assert got['realChains'][0] > 50 and got['realChains'][1] > 0.9 * got['realChains'][0] and got['realChains'][2] == [], got['realChains']
            assert got['trusted'] == [[True, 'Lista de teste', 'Raiz Teste', ['Fulano Teste', 'Raiz Teste'], 'ICP-Brasil PA_PAdES_AD_RB v1.1', True]], got['trusted']
            assert got['selfSignedUnderTestList'] == [None], got['selfSignedUnderTestList']
            assert got['backdatedCheck'] == [[None, True]], got['backdatedCheck']
            assert 'not meant for signatures' in got['caSignedCheck'], got['caSignedCheck']
            assert 'unknown signature policy' in got['unknownPolicy'].lower(), got['unknownPolicy']
            assert 'password' in got['wrongPassword'].lower(), got['wrongPassword']
            assert got['locked'] == [[True, True]], got['locked']
            assert 'locked' in got['resign'].lower(), got['resign']
            assert got['lockedChanged'] == [False], got['lockedChanged']
            assert len(got['widget']) == 1 and got['widget'][0][2] - got['widget'][0][0] == 250, got['widget']
            # the check panel never shows a signature followed by later changes as intact (green)
            import base64
            page.set_input_files('#pdfInput', files=[{'name': 'twice.pdf', 'mimeType': 'application/pdf', 'buffer': base64.b64decode(got['twice'])}])
            page.click('[data-tab=check]')
            page.click('#checkBtn')
            page.wait_for_function("() => document.querySelectorAll('#checkList li').length === 2")
            heads = page.eval_on_selector_all('#checkList li > span', 'els => els.map(e => e.className)')
            assert heads == ['bad', 'ok'], heads
            # official validation: opened by the user from the warning dialog, never fetched by the page
            requests: list[str] = []
            page.on('request', lambda r: requests.append(r.url))
            page.evaluate("() => { window.__opened = []; window.open = (u, t, f) => { window.__opened.push([u, t, f]); return null; }; }")
            page.click('[data-tab=check]')
            page.click('#itiBtn')
            assert page.evaluate("() => document.getElementById('itiDialog').open"), 'warning dialog did not open'
            assert 'servers' in page.inner_text('#itiDialog') and page.evaluate('() => window.__opened.length') == 0
            page.click('#itiCancel')
            assert page.evaluate('() => window.__opened.length') == 0
            page.click('#itiBtn'); page.click('#itiOpen')
            assert page.evaluate('() => window.__opened') == [['https://validar.iti.gov.br/', '_blank', 'noopener,noreferrer']]
            assert not any('iti.gov.br' in u for u in requests), requests
            # the page itself loads without errors and Home reaches it through Advanced tools (web edition only)
            home = (ROOT / 'index.html').read_text(encoding='utf-8')
            catalog = (ROOT / 'assets' / 'advanced-tools.js').read_text(encoding='utf-8')
            assert "href:'./labs/pdf/index.html'" in catalog and 'id="advancedToolsButton" class="quick-tool"' in home
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
    print('PDF tools (beta): OCR, digital signatures and checks passed')


if __name__ == '__main__':
    main()
