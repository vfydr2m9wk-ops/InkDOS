/* InkDOS PDF Lab (beta): digital signatures with an A1 certificate (.pfx/.p12) and signature checks.
 *
 * Signing (PAdES baseline B-B, /ETSI.CAdES.detached) appends an incremental update to the original bytes (earlier signatures stay valid):
 * a signature dictionary, a signature field widget on a page, the page or
 * its /Annots array and the AcroForm (or the catalog) rewritten with the new field, and a cross-
 * reference section of the same kind as the file's last one (table or stream). The CMS SignedData
 * is assembled with node-forge ASN.1 over the bytes outside /Contents; expired, not-yet-valid,
 * weak (< 2048-bit) or non-signing certificates are refused, and every new signature must pass
 * the check below before it is returned.
 *
 * Checking reads every /ByteRange signature in the file: the message digest of the signed bytes,
 * the signer's signature over its signed attributes (RSA PKCS#1 v1.5 and ECDSA through WebCrypto),
 * the signer certificate and whether the file was changed after signing. The byte range may leave
 * out only the /Contents hex string, the signing-certificate attribute must name the signer, SHA-1
 * digests are refused, and the chain carried in the signature is checked issuer by issuer. The chain
 * is not checked against a trust list, revocation or timestamps in this beta.
 */
(function (global) {
  'use strict';

  const latin1 = new TextDecoder('latin1');
  const enc = s => { const out = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i) & 255; return out; };
  const concat = parts => { const n = parts.reduce((a, p) => a + p.length, 0), out = new Uint8Array(n); let o = 0; for (const p of parts) { out.set(p, o); o += p.length; } return out; };
  const binary = bytes => { let s = ''; for (let i = 0; i < bytes.length; i += 32768) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 32768)); return s; };
  const pad = (n, w) => String(n).padStart(w, '0');

  // local date and time with the UTC offset, e.g. 04/10/2026 14:05:09 (UTC-03:00)
  function localStamp(d) {
    const off = -d.getTimezoneOffset(), sign = off >= 0 ? '+' : '-', a = Math.abs(off);
    return pad(d.getDate(), 2) + '/' + pad(d.getMonth() + 1, 2) + '/' + d.getFullYear() + ' ' + pad(d.getHours(), 2) + ':' + pad(d.getMinutes(), 2) + ':' + pad(d.getSeconds(), 2) +
      ' (UTC' + sign + pad(Math.floor(a / 60), 2) + ':' + pad(a % 60, 2) + ')';
  }

  function pdfDate(d) {
    return 'D:' + d.getUTCFullYear() + pad(d.getUTCMonth() + 1, 2) + pad(d.getUTCDate(), 2) + pad(d.getUTCHours(), 2) + pad(d.getUTCMinutes(), 2) + pad(d.getUTCSeconds(), 2) + 'Z';
  }

  function lastStartXref(text) {
    const i = text.lastIndexOf('startxref');
    if (i < 0) throw new Error('The PDF has no cross-reference start (startxref).');
    const m = /startxref\s+(\d+)/.exec(text.slice(i, i + 40));
    if (!m) throw new Error('The PDF cross-reference start is unreadable.');
    return Number(m[1]);
  }

  // ---------------------------------------------------------------------------------------------
  // Certificate (.pfx/.p12)

  function readCertificate(p12Bytes, password) {
    const forge = global.forge;
    let p12;
    try {
      p12 = forge.pkcs12.pkcs12FromAsn1(forge.asn1.fromDer(binary(p12Bytes)), password || '');
    } catch (e) {
      throw new Error(/mac|password|Invalid/i.test(String(e && e.message)) ? 'Wrong certificate password or unreadable .pfx/.p12 file.' : 'Unreadable certificate file: ' + (e && e.message));
    }
    const keyBags = [...(p12.getBags({ bagType: forge.pki.oids.pkcs8ShroudedKeyBag })[forge.pki.oids.pkcs8ShroudedKeyBag] || []),
      ...(p12.getBags({ bagType: forge.pki.oids.keyBag })[forge.pki.oids.keyBag] || [])];
    const certs = (p12.getBags({ bagType: forge.pki.oids.certBag })[forge.pki.oids.certBag] || []).map(b => b.cert).filter(Boolean);
    const key = keyBags.map(b => b.key).find(Boolean);
    if (!key || !key.n) throw new Error('No private key in the certificate file (only RSA keys are supported in this beta).');
    if (!certs.length) throw new Error('No certificate in the certificate file.');
    const cert = certs.find(c => c.publicKey && c.publicKey.n && c.publicKey.n.equals(key.n) && c.publicKey.e.equals(key.e));
    if (!cert) throw new Error('The private key in the certificate file does not match any of its certificates.');
    // signer certificate first, then the rest of the chain found in the file
    const chain = [cert, ...certs.filter(c => c !== cert)];
    return { key, cert, chain, subject: (cert.subject.getField('CN') || {}).value || '', notBefore: cert.validity.notBefore, notAfter: cert.validity.notAfter };
  }

  // refuse certificates that cannot produce a valid signature now
  function assertUsable(certificate, now) {
    const { cert, key } = certificate;
    if (now < cert.validity.notBefore) throw new Error('The certificate is not valid yet (valid from ' + cert.validity.notBefore.toISOString().slice(0, 10) + ').');
    if (now > cert.validity.notAfter) throw new Error('The certificate expired on ' + cert.validity.notAfter.toISOString().slice(0, 10) + ': it cannot sign.');
    if (key.n.bitLength() < 2048) throw new Error('The certificate key is shorter than 2048 bits: too weak to sign.');
    const usage = cert.getExtension('keyUsage');
    if (usage && !usage.digitalSignature && !usage.nonRepudiation) throw new Error('The certificate is not allowed to make digital signatures (key usage).');
  }

  // CMS SignedData for PAdES baseline (ETSI.CAdES.detached): signed attributes are content-type,
  // message-digest and signing-certificate-v2 (binds the signer certificate to the signature); the
  // claimed signing time is the signature dictionary's /M, so no signing-time attribute is added.
  function buildCms(signedBytes, certificate) {
    const forge = global.forge, asn1 = forge.asn1, U = asn1.Class.UNIVERSAL, T = asn1.Type, C = asn1.Class.CONTEXT_SPECIFIC;
    const seq = v => asn1.create(U, T.SEQUENCE, true, v), set = v => asn1.create(U, T.SET, true, v);
    const oid = o => asn1.create(U, T.OID, false, asn1.oidToDer(o).getBytes());
    const octets = s => asn1.create(U, T.OCTETSTRING, false, s);
    const int = n => asn1.create(U, T.INTEGER, false, asn1.integerToDer(n).getBytes());
    const der = a => asn1.toDer(a).getBytes();
    const sha256 = s => { const md = forge.md.sha256.create(); md.update(s); return md; };
    const certAsn1 = c => forge.pki.certificateToAsn1(c);
    // issuer and serial exactly as encoded in the certificate
    const tbs = certificate.cert.tbsCertificate, f = tbs.value.slice(tbs.value[0].tagClass === C ? 1 : 0);
    const serial = f[0], issuer = f[2];
    const essCertIdV2 = seq([octets(sha256(der(certAsn1(certificate.cert))).digest().getBytes()), seq([seq([asn1.create(C, 4, true, [issuer])]), serial])]);
    const attrs = [
      [OID.contentType, oid(OID.data)],
      [OID.messageDigest, octets(sha256(binary(signedBytes)).digest().getBytes())],
      [OID.signingCertificateV2, seq([seq([essCertIdV2])])]
    ].map(([type, value]) => seq([oid(type), set([value])]));
    // DER SET OF: elements in ascending order of their encodings
    attrs.sort((a, b) => { const x = der(a), y = der(b); return x < y ? -1 : x > y ? 1 : 0; });
    const signature = certificate.key.sign(sha256(der(set(attrs))));
    const signerInfo = seq([int(1), seq([issuer, serial]), seq([oid(OID.sha256)]), asn1.create(C, 0, true, attrs),
      seq([oid(OID.sha256WithRSA), asn1.create(U, T.NULL, false, '')]), octets(signature)]);
    const signedData = seq([int(1), set([seq([oid(OID.sha256)])]), seq([oid(OID.data)]),
      asn1.create(C, 0, true, certificate.chain.map(certAsn1)), set([signerInfo])]);
    return der(seq([oid(OID.signedData), asn1.create(C, 0, true, [signedData])]));
  }

  // ---------------------------------------------------------------------------------------------
  // Signing (incremental update)

  async function signPdf(bytes, options) {
    const PDFLib = global.PDFLib, forge = global.forge;
    const { PDFName, PDFArray, PDFDict, PDFRef, PDFHexString, PDFNumber } = PDFLib;
    const o = Object.assign({ reason: '', location: '', contact: '', pageIndex: 0, placeholderBytes: 12000, now: new Date(), visible: null, lock: false, labels: {} }, options);
    const certificate = readCertificate(o.p12, o.password);
    assertUsable(certificate, o.now);
    let doc;
    try { doc = await PDFLib.PDFDocument.load(bytes, { updateMetadata: false }); } catch (e) {
      throw new Error(/encrypt/i.test(String(e && e.message)) ? 'Encrypted PDFs cannot be signed in this beta.' : 'The PDF could not be read: ' + (e && e.message));
    }
    // a certification that allows no changes ends the document's signing; a lock must be the first signature
    const existing = signatureFields(bytes);
    if (existing.some(f => f.docmdp === 1)) throw new Error('This document is locked by a certification signature: it cannot be signed again.');
    if (o.lock && existing.length) throw new Error('Only the first signature can lock the document; this PDF is already signed.');
    const ctx = doc.context, text = latin1.decode(bytes);
    const prev = lastStartXref(text), classic = text.slice(prev, prev + 4) === 'xref';
    const catalogRef = ctx.trailerInfo.Root, infoRef = ctx.trailerInfo.Info, id = ctx.trailerInfo.ID;
    const page = doc.getPage(Math.min(Math.max(0, o.pageIndex | 0), doc.getPageCount() - 1));
    // new objects are numbered after everything in the file, including object streams and xref streams
    const sizeMatch = /\/Size\s+(\d+)/.exec(text.slice(prev, prev + 400000));
    let next = Math.max(ctx.largestObjectNumber + 1, sizeMatch ? Number(sizeMatch[1]) : 0);
    const sigNum = next++, widgetNum = next++, widgetRef = PDFRef.of(widgetNum), sigRef = PDFRef.of(sigNum);
    const apNum = o.visible ? next++ : 0, fontNum = o.visible ? next++ : 0;
    const fieldCount = (() => { const af = doc.catalog.lookup(PDFName.of('AcroForm')); const f = af instanceof PDFDict ? af.lookup(PDFName.of('Fields')) : null; return f instanceof PDFArray ? f.size() : 0; })();
    const rewritten = []; // [objectNumber, pdf syntax]

    // the page (or its indirect /Annots array) lists the new widget
    const annots = page.node.get(PDFName.of('Annots'));
    if (annots instanceof PDFRef) {
      const arr = ctx.lookup(annots).clone(ctx); arr.push(widgetRef); rewritten.push([annots.objectNumber, arr.toString()]);
    } else {
      const node = page.node.clone(ctx), arr = annots instanceof PDFArray ? annots.clone(ctx) : ctx.obj([]);
      arr.push(widgetRef); node.set(PDFName.of('Annots'), arr); rewritten.push([page.ref.objectNumber, node.toString()]);
    }
    // the AcroForm (indirect, or inside the catalog) lists the new field and declares signatures
    const afEntry = doc.catalog.get(PDFName.of('AcroForm'));
    const withField = dict => {
      const fields = dict.lookup(PDFName.of('Fields'));
      const arr = fields instanceof PDFArray ? fields.clone(ctx) : ctx.obj([]); arr.push(widgetRef);
      dict.set(PDFName.of('Fields'), arr); dict.set(PDFName.of('SigFlags'), PDFNumber.of(3)); return dict;
    };
    let cat = null;
    if (afEntry instanceof PDFRef) {
      rewritten.push([afEntry.objectNumber, withField(ctx.lookup(afEntry).clone(ctx)).toString()]);
    } else {
      cat = doc.catalog.clone(ctx);
      cat.set(PDFName.of('AcroForm'), withField(afEntry instanceof PDFDict ? afEntry.clone(ctx) : ctx.obj({})));
    }
    // certification (DocMDP, P 1): readers report any later change to the document as invalidating it
    if (o.lock) { cat = cat || doc.catalog.clone(ctx); cat.set(PDFName.of('Perms'), ctx.obj({ DocMDP: sigRef })); }
    if (cat) rewritten.push([catalogRef.objectNumber, cat.toString()]);

    const hexText = s => PDFHexString.fromText(String(s)).toString();
    const contentsLen = o.placeholderBytes * 2, brPlaceholder = '[0 0000000000 0000000000 0000000000]';
    const sigDict = '<< /Type /Sig /Filter /Adobe.PPKLite /SubFilter /ETSI.CAdES.detached /ByteRange ' + brPlaceholder +
      ' /Contents <' + '0'.repeat(contentsLen) + '> /M (' + pdfDate(o.now) + ') /Name ' + hexText(certificate.subject) +
      (o.reason ? ' /Reason ' + hexText(o.reason) : '') + (o.location ? ' /Location ' + hexText(o.location) : '') +
      (o.contact ? ' /ContactInfo ' + hexText(o.contact) : '') +
      (o.lock ? ' /Reference [<< /Type /SigRef /TransformMethod /DocMDP /TransformParams << /Type /TransformParams /P 1 /V /1.2 >> >>]' : '') + ' >>';
    // visible signature: a box with the signer and the signing date and time
    let rect = '[0 0 0 0]', extra = [];
    if (o.visible) {
      const box = page.getCropBox ? page.getCropBox() : page.getMediaBox(), W = 250, H = 50, m = 24;
      const pos = String(o.visible.position || 'bottom-left');
      const x = pos.endsWith('right') ? box.x + box.width - W - m : box.x + m, y = pos.startsWith('top') ? box.y + box.height - H - m : box.y + m;
      rect = '[' + [x, y, x + W, y + H].map(v => v.toFixed(2)).join(' ') + ']';
      const pdfText = t => '(' + [...String(t)].map(ch => { const c = ch.charCodeAt(0); return c > 255 ? '?' : ch === '(' || ch === ')' || ch === '\\' ? '\\' + ch : c < 32 || c > 126 ? '\\' + c.toString(8).padStart(3, '0') : ch; }).join('') + ')';
      const lines = [o.labels.signedBy || 'Digitally signed by', certificate.subject, (o.labels.date || 'Date') + ': ' + localStamp(o.now)];
      const stream = 'q 0.96 0.97 0.98 rg 0 0 ' + W + ' ' + H + ' re f 0.55 0.6 0.66 RG 0.8 w 0.4 0.4 ' + (W - 0.8) + ' ' + (H - 0.8) + ' re S Q\n' +
        'BT 0.12 0.14 0.18 rg /F1 8 Tf 6 ' + (H - 13) + ' Td ' + pdfText(lines[0]) + ' Tj /F1 10 Tf 0 -14 Td ' + pdfText(lines[1]) + ' Tj /F1 8 Tf 0 -14 Td ' + pdfText(lines[2]) + ' Tj ET';
      extra = [[apNum, '<< /Type /XObject /Subtype /Form /BBox [0 0 ' + W + ' ' + H + '] /Resources << /Font << /F1 ' + fontNum + ' 0 R >> >> /Length ' + stream.length + ' >>\nstream\n' + stream + '\nendstream'],
        [fontNum, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']];
    }
    const widget = '<< /Type /Annot /Subtype /Widget /FT /Sig /T ' + hexText('Signature' + (fieldCount + 1)) + ' /V ' + sigRef + ' /F 132 /Rect ' + rect + ' /P ' + page.ref +
      (o.visible ? ' /AP << /N ' + apNum + ' 0 R >>' : '') + ' >>';
    const objects = [[sigNum, sigDict], [widgetNum, widget], ...extra, ...rewritten].sort((a, b) => a[0] - b[0]);

    // body of the update
    let body = '\n';
    const offsets = new Map();
    for (const [num, src] of objects) { offsets.set(num, bytes.length + body.length); body += num + ' 0 obj\n' + src + '\nendobj\n'; }
    const trailerTail = ' /Root ' + catalogRef + (infoRef ? ' /Info ' + infoRef : '') + (id ? ' /ID ' + id.toString() : '') + ' /Prev ' + prev;
    let tail;
    if (classic) {
      const xrefAt = bytes.length + body.length;
      let x = 'xref\n';
      for (const [num] of objects) x += num + ' 1\n' + pad(offsets.get(num), 10) + ' 00000 n\r\n';
      tail = enc(x + 'trailer\n<< /Size ' + next + trailerTail + ' >>\nstartxref\n' + xrefAt + '\n%%EOF\n');
    } else {
      const xrefNum = next++, xrefAt = bytes.length + body.length;
      offsets.set(xrefNum, xrefAt);
      const nums = [...objects.map(x => x[0]), xrefNum].sort((a, b) => a - b), rows = new Uint8Array(nums.length * 7);
      nums.forEach((n, i) => { const off = offsets.get(n); rows.set([1, (off >>> 24) & 255, (off >>> 16) & 255, (off >>> 8) & 255, off & 255, 0, 0], i * 7); });
      const head = xrefNum + ' 0 obj\n<< /Type /XRef /Size ' + next + ' /Index [' + nums.map(n => n + ' 1').join(' ') + '] /W [1 4 2]' + trailerTail + ' /Length ' + rows.length + ' >>\nstream\n';
      tail = concat([enc(head), rows, enc('\nendstream\nendobj\nstartxref\n' + xrefAt + '\n%%EOF\n')]);
    }
    const out = concat([bytes, enc(body), tail]);

    // byte range around /Contents of the new signature dictionary
    const sigAt = offsets.get(sigNum), region = latin1.decode(out.subarray(sigAt, sigAt + sigDict.length + 40));
    const cStart = sigAt + region.indexOf('/Contents <') + '/Contents '.length, cEnd = cStart + contentsLen + 2;
    const range = [0, cStart, cEnd, out.length - cEnd];
    const brText = ('[' + range.join(' ') + ']').padEnd(brPlaceholder.length, ' ');
    out.set(enc(brText), sigAt + region.indexOf(brPlaceholder));

    // CMS SignedData (detached) over the two ranges
    const signed = concat([out.subarray(0, cStart), out.subarray(cEnd)]);
    const hex = forge.util.bytesToHex(buildCms(signed, certificate));
    if (hex.length > contentsLen) throw new Error('The signature is larger than its reserved space.');
    out.set(enc(hex.padEnd(contentsLen, '0')), cStart + 1);
    // never hand out a signature this module itself would not accept
    const own = (await checkPdf(out)).pop();
    if (!own || !own.ok) throw new Error('The new signature failed its own check: ' + ((own && own.problems.join(' ')) || 'not found') + ' The file was not changed.');
    return { bytes: out, signer: certificate.subject, notAfter: certificate.notAfter };
  }

  // ---------------------------------------------------------------------------------------------
  // Checking existing signatures

  const OID = {
    sha1: '1.3.14.3.2.26', sha256: '2.16.840.1.101.3.4.2.1', sha384: '2.16.840.1.101.3.4.2.2', sha512: '2.16.840.1.101.3.4.2.3',
    messageDigest: '1.2.840.113549.1.9.4', signingTime: '1.2.840.113549.1.9.5', rsa: '1.2.840.113549.1.1.1', ec: '1.2.840.10045.2.1',
    p256: '1.2.840.10045.3.1.7', p384: '1.3.132.0.34', p521: '1.3.132.0.35', commonName: '2.5.4.3',
    data: '1.2.840.113549.1.7.1', signedData: '1.2.840.113549.1.7.2', contentType: '1.2.840.113549.1.9.3', sha256WithRSA: '1.2.840.113549.1.1.11',
    signingCertificate: '1.2.840.113549.1.9.16.2.12', signingCertificateV2: '1.2.840.113549.1.9.16.2.47', timeStampToken: '1.2.840.113549.1.9.16.2.14',
    basicConstraints: '2.5.29.19', subjectKeyIdentifier: '2.5.29.14'
  };
  const HASH = { [OID.sha1]: 'SHA-1', [OID.sha256]: 'SHA-256', [OID.sha384]: 'SHA-384', [OID.sha512]: 'SHA-512' };
  // certificate signature algorithms (RSA PKCS#1 v1.5 and ECDSA) and their digests
  const CERT_SIG = { '1.2.840.113549.1.1.5': 'SHA-1', '1.2.840.113549.1.1.11': 'SHA-256', '1.2.840.113549.1.1.12': 'SHA-384', '1.2.840.113549.1.1.13': 'SHA-512',
    '1.2.840.10045.4.1': 'SHA-1', '1.2.840.10045.4.3.2': 'SHA-256', '1.2.840.10045.4.3.3': 'SHA-384', '1.2.840.10045.4.3.4': 'SHA-512' };

  // PDF date (D:YYYYMMDDHHmmSSOHH'mm) to Date; null when unreadable
  function parsePdfDate(s) {
    const m = /^D?:?(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?([Zz+-])?(\d{2})?'?(\d{2})?/.exec(String(s || '').trim());
    if (!m) return null;
    const n = i => Number(m[i] || 0), off = m[7] === '+' || m[7] === '-' ? (m[7] === '-' ? -1 : 1) * (n(8) * 60 + n(9)) : 0;
    const t = Date.UTC(n(1), (m[2] ? n(2) : 1) - 1, m[3] ? n(3) : 1, n(4), n(5), n(6)) - off * 60000;
    return Number.isFinite(t) ? new Date(t) : null;
  }

  function signatureFields(bytes) {
    const text = latin1.decode(bytes), out = [];
    const re = /\/ByteRange\s*\[\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*\]/g;
    let m;
    while ((m = re.exec(text))) {
      const start = text.lastIndexOf(' obj', m.index), end = text.indexOf('endobj', m.index);
      const seg = text.slice(Math.max(0, start), end < 0 ? m.index + 200000 : end);
      const c = /\/Contents\s*<([0-9A-Fa-f\s]*)>/.exec(seg);
      if (!c) continue;
      const str = key => { const r = new RegExp('\\/' + key + '\\s*(\\((?:\\\\.|[^\\\\)])*\\)|<[0-9A-Fa-f\\s]*>)').exec(seg); return r ? decodePdfString(r[1]) : ''; };
      out.push({ range: m.slice(1, 5).map(Number), contents: c[1].replace(/\s+/g, ''), subFilter: (/\/SubFilter\s*\/([A-Za-z0-9.]+)/.exec(seg) || [])[1] || '',
        name: str('Name'), reason: str('Reason'), location: str('Location'), time: str('M'),
        docmdp: /\/TransformMethod\s*\/DocMDP/.test(seg) ? Number((/\/P\s+(\d)/.exec(seg.slice(seg.indexOf('/TransformParams'))) || [])[1] || 2) : 0 });
    }
    return out;
  }

  function decodePdfString(s) {
    let b;
    if (s[0] === '<') { const h = s.slice(1, -1).replace(/\s+/g, ''); b = []; for (let i = 0; i < h.length; i += 2) b.push(parseInt(h.substr(i, 2).padEnd(2, '0'), 16)); }
    else { b = []; const t = s.slice(1, -1); for (let i = 0; i < t.length; i++) { if (t[i] === '\\' && i + 1 < t.length) { const n = t[++i], esc = { n: 10, r: 13, t: 9, b: 8, f: 12 }[n]; b.push(esc !== undefined ? esc : n.charCodeAt(0)); } else b.push(t.charCodeAt(i)); } }
    if (b[0] === 254 && b[1] === 255) { let r = ''; for (let i = 2; i + 1 < b.length; i += 2) r += String.fromCharCode((b[i] << 8) | b[i + 1]); return r; }
    return String.fromCharCode.apply(null, b);
  }

  // minimal X.509 reading with forge's generic ASN.1 parser (works for RSA and EC certificates)
  function certInfo(certAsn1) {
    const forge = global.forge, asn1 = forge.asn1, tbs = certAsn1.value[0], f = tbs.value.slice(tbs.value[0].tagClass === asn1.Class.CONTEXT_SPECIFIC ? 1 : 0);
    const name = n => { for (const rdn of n.value) for (const at of rdn.value) if (asn1.derToOid(at.value[0].value) === OID.commonName) return String(at.value[1].value); return ''; };
    const time = t => (t.type === asn1.Type.UTCTIME ? asn1.utcTimeToDate : asn1.generalizedTimeToDate)(t.value);
    const der = a => asn1.toDer(a).getBytes();
    // extensions: CA flag (null when absent) and subject key identifier
    let ca = null, ski = '';
    const extList = tbs.value.find(v => v.tagClass === asn1.Class.CONTEXT_SPECIFIC && v.type === 3);
    for (const ext of (extList && extList.value[0] ? extList.value[0].value : [])) {
      try {
        const id = asn1.derToOid(ext.value[0].value), inner = asn1.fromDer(ext.value[ext.value.length - 1].value);
        if (id === OID.basicConstraints) ca = !!(inner.value[0] && inner.value[0].type === asn1.Type.BOOLEAN && inner.value[0].value !== '\x00');
        if (id === OID.subjectKeyIdentifier) ski = forge.util.bytesToHex(inner.value);
      } catch (_) { /* unreadable extension: ignored */ }
    }
    const bits = certAsn1.value[2], sigRaw = 'bitStringContents' in bits ? bits.bitStringContents : bits.value;
    let keyBits = 0;
    try { const pk = f[5].value[1].value; if (Array.isArray(pk) && pk[0] && Array.isArray(pk[0].value)) keyBits = pk[0].value[0].value.replace(/^\x00+/, '').length * 8; } catch (_) { /* EC or unreadable */ }
    return { serial: forge.util.bytesToHex(f[0].value), issuer: name(f[2]), notBefore: time(f[3].value[0]), notAfter: time(f[3].value[1]), subject: name(f[4]), spki: f[5],
      der: der(certAsn1), tbsDer: der(tbs), issuerDer: der(f[2]), subjectDer: der(f[4]), sigAlg: asn1.derToOid(certAsn1.value[1].value[0].value),
      sig: enc(sigRaw.slice(1)), ca, ski, keyBits };
  }

  // does `issuer` sign `cert`? true / false, or null when the algorithm is not supported
  async function certSignedBy(cert, issuer) {
    const hashName = CERT_SIG[cert.sigAlg];
    if (!hashName) return null;
    try { return await verifySignature(issuer.spki, hashName, enc(cert.tbsDer), cert.sig); } catch (_) { return false; }
  }

  // chain from the signer up through the certificates carried in the signature (no trust list)
  async function buildChain(signer, certs, when) {
    const chain = [signer];
    let cur = signer, status = 'incomplete';
    for (let depth = 0; depth < 10; depth++) {
      if (cur.subjectDer === cur.issuerDer) { const ok = await certSignedBy(cur, cur); status = ok === true ? 'root' : ok === null ? 'unsupported' : 'broken'; break; }
      const parent = certs.find(c => c !== cur && c.subjectDer === cur.issuerDer);
      if (!parent) break;
      const ok = await certSignedBy(cur, parent);
      if (ok !== true) { status = ok === null ? 'unsupported' : 'broken'; break; }
      if (parent.ca === false) { status = 'broken'; break; }
      chain.push(parent); cur = parent;
    }
    return { names: chain.map(c => c.subject || c.serial), status, validAtSigning: chain.every(c => when >= c.notBefore && when <= c.notAfter), weakHash: chain.some(c => CERT_SIG[c.sigAlg] === 'SHA-1' && c.subjectDer !== c.issuerDer) };
  }

  async function digest(alg, bytes) { return new Uint8Array(await crypto.subtle.digest(alg, bytes)); }
  const same = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);

  async function verifySignature(spkiAsn1, hashName, data, sig) {
    const forge = global.forge, algOid = forge.asn1.derToOid(spkiAsn1.value[0].value[0].value), der = enc(forge.asn1.toDer(spkiAsn1).getBytes());
    if (algOid === OID.rsa) {
      const key = await crypto.subtle.importKey('spki', der, { name: 'RSASSA-PKCS1-v1_5', hash: hashName }, false, ['verify']);
      return crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, sig, data);
    }
    if (algOid === OID.ec) {
      const curveOid = forge.asn1.derToOid(spkiAsn1.value[0].value[1].value), curve = { [OID.p256]: 'P-256', [OID.p384]: 'P-384', [OID.p521]: 'P-521' }[curveOid];
      if (!curve) return null;
      const key = await crypto.subtle.importKey('spki', der, { name: 'ECDSA', namedCurve: curve }, false, ['verify']);
      const size = { 'P-256': 32, 'P-384': 48, 'P-521': 66 }[curve], seq = forge.asn1.fromDer(binary(sig));
      const part = v => { const b = enc(v.value).filter((x, i, a) => !(i === 0 && x === 0 && a.length > size)); const r = new Uint8Array(size); r.set(b.slice(-size), size - Math.min(size, b.length)); return r; };
      return crypto.subtle.verify({ name: 'ECDSA', hash: hashName }, key, concat([part(seq.value[0]), part(seq.value[1])]), data);
    }
    return null;
  }

  async function checkPdf(bytes) {
    const forge = global.forge, asn1 = forge.asn1, CTX = asn1.Class.CONTEXT_SPECIFIC, results = [];
    const oidOf = at => asn1.derToOid(at.value[0].value);
    const isHex = x => (x >= 48 && x <= 57) || (x >= 65 && x <= 70) || (x >= 97 && x <= 102) || x === 32 || x === 9 || x === 10 || x === 13 || x === 12;
    for (const f of signatureFields(bytes)) {
      const r = { name: f.name, reason: f.reason, location: f.location, time: f.time, subFilter: f.subFilter, coversWholeFile: f.range[2] + f.range[3] === bytes.length, locked: f.docmdp === 1, problems: [], notes: [] };
      try {
        const [a, b, c, d] = f.range;
        if (a !== 0 || b <= 0 || c <= b || d < 0 || c + d > bytes.length) throw new Error('Invalid byte range.');
        // the only unsigned bytes must be the hex string of this signature's /Contents
        const gap = bytes.subarray(b, c);
        if (gap[0] !== 60 || gap[gap.length - 1] !== 62 || !gap.subarray(1, -1).every(isHex)) throw new Error('The signature byte range leaves out more than the signature itself.');
        const gapHex = latin1.decode(gap.subarray(1, -1)).replace(/\s+/g, '');
        if (gapHex !== f.contents) throw new Error('The signature byte range does not match its /Contents.');
        const signed = concat([bytes.subarray(a, a + b), bytes.subarray(c, c + d)]);
        const ci = asn1.fromDer(forge.util.hexToBytes(gapHex), { parseAllBytes: false, strict: false });
        if (asn1.derToOid(ci.value[0].value) !== OID.signedData) throw new Error('The signature is not CMS SignedData.');
        const sd = ci.value[1].value[0], parts = sd.value;
        const certSet = parts.find(p => p.tagClass === CTX && p.type === 0);
        const si = parts[parts.length - 1].value[0].value;
        const certs = certSet ? certSet.value.map(certInfo) : [];
        // signer certificate: by issuer and serial number, or by subject key identifier
        const sid = si[1];
        const cert = sid.tagClass === CTX ? certs.find(x => x.ski && x.ski === forge.util.bytesToHex(sid.value))
          : certs.find(x => x.issuerDer === asn1.toDer(sid.value[0]).getBytes() && x.serial === forge.util.bytesToHex(sid.value[1].value));
        const hashName = HASH[asn1.derToOid(si[2].value[0].value)];
        if (!hashName) throw new Error('Unsupported digest algorithm.');
        let i = 3, attrs = null;
        if (si[i].tagClass === CTX && si[i].type === 0) attrs = si[i++];
        i++; // signature algorithm
        const sig = enc(si[i].value), unsigned = si[i + 1] && si[i + 1].tagClass === CTX && si[i + 1].type === 1 ? si[i + 1].value : [];
        const docHash = await digest(hashName, signed);
        let certBound = null;
        if (attrs) {
          const md = attrs.value.find(at => oidOf(at) === OID.messageDigest);
          r.integrity = !!md && same(enc(md.value[1].value[0].value), docHash);
          const st = attrs.value.find(at => oidOf(at) === OID.signingTime);
          if (st) { const t = st.value[1].value[0]; r.signedAt = (t.type === asn1.Type.UTCTIME ? asn1.utcTimeToDate : asn1.generalizedTimeToDate)(t.value); }
          // signing-certificate(-v2): the signed attributes name the certificate by its hash
          const sc = attrs.value.find(at => oidOf(at) === OID.signingCertificateV2 || oidOf(at) === OID.signingCertificate);
          if (sc && cert) {
            const id = sc.value[1].value[0].value[0].value[0].value, v2 = oidOf(sc) === OID.signingCertificateV2;
            const alg = v2 && id[0].type === asn1.Type.SEQUENCE ? HASH[asn1.derToOid(id[0].value[0].value)] : (v2 ? 'SHA-256' : 'SHA-1');
            const certHash = (v2 && id[0].type === asn1.Type.SEQUENCE ? id[1] : id[0]).value;
            certBound = !!alg && same(enc(certHash), await digest(alg, enc(cert.der)));
          } else if (!sc) r.notes.push('no-signing-certificate');
          const setDer = asn1.toDer(asn1.create(asn1.Class.UNIVERSAL, asn1.Type.SET, true, attrs.value)).getBytes();
          r.signatureValid = cert ? await verifySignature(cert.spki, hashName, enc(setDer), sig) : null;
        } else {
          r.integrity = null;
          r.signatureValid = cert ? await verifySignature(cert.spki, hashName, signed, sig) : null;
        }
        r.timestamped = unsigned.some(at => oidOf(at) === OID.timeStampToken);
        r.notes.push(r.timestamped ? 'timestamp-not-checked' : 'no-timestamp');
        if (!r.signedAt) r.signedAt = parsePdfDate(f.time) || undefined;
        if (cert) {
          Object.assign(r, { signer: cert.subject, issuer: cert.issuer, notBefore: cert.notBefore, notAfter: cert.notAfter });
          const when = r.signedAt || new Date();
          r.certificateValidAtSigning = when >= cert.notBefore && when <= cert.notAfter;
          const chain = await buildChain(cert, certs, when);
          r.chain = chain.names; r.chainStatus = chain.status;
          if (chain.status === 'broken') r.problems.push('The certificate chain in the signature is not consistent (a certificate is not signed by its issuer).');
          if (chain.status === 'incomplete') r.notes.push('chain-incomplete');
          if (chain.status === 'unsupported') r.notes.push('chain-unsupported');
          if (!chain.validAtSigning && r.certificateValidAtSigning) r.problems.push('A certificate in the chain was not valid at signing time.');
          if (chain.weakHash) r.notes.push('weak-chain-hash');
          if (cert.keyBits && cert.keyBits < 2048) r.notes.push('weak-key');
          r.chainValidAtSigning = chain.validAtSigning;
        } else r.problems.push('The signer certificate is missing from the signature.');
        if (certBound === false) r.problems.push('The signed attributes name a different certificate than the one used to sign.');
        if (hashName === 'SHA-1') r.problems.push('SHA-1 digests are no longer accepted for signatures.');
        if (r.integrity === false) r.problems.push('The signed content does not match the document.');
        if (r.signatureValid === null && cert) r.problems.push('Signature algorithm not supported by this check.');
        if (r.signatureValid === false) r.problems.push('The cryptographic signature does not verify.');
        r.ok = r.integrity !== false && r.signatureValid === true && certBound !== false && hashName !== 'SHA-1' &&
          r.certificateValidAtSigning !== false && r.chainValidAtSigning !== false && r.chainStatus !== 'broken';
        if (r.locked && !r.coversWholeFile) { r.ok = false; r.problems.push('The document was changed after a certification that allows no changes.'); }
      } catch (e) {
        r.ok = false; r.problems.push(String(e && e.message || e));
      }
      results.push(r);
    }
    return results;
  }

  global.InkDOSPdfLabSign = Object.freeze({ signPdf, checkPdf, readCertificate, isLocked: bytes => signatureFields(bytes).some(f => f.docmdp === 1), _test: { signatureFields, decodePdfString } });
})(globalThis);
