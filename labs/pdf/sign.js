/* InkDOS PDF Lab (beta): digital signatures with an A1 certificate (.pfx/.p12) and signature checks.
 *
 * Signing appends an incremental update to the original bytes (earlier signatures stay valid):
 * a signature dictionary (/adbe.pkcs7.detached), a signature field widget on a page, the page or
 * its /Annots array and the AcroForm (or the catalog) rewritten with the new field, and a cross-
 * reference section of the same kind as the file's last one (table or stream). The CMS SignedData
 * is built with node-forge over the bytes outside /Contents.
 *
 * Checking reads every /ByteRange signature in the file: the message digest of the signed bytes,
 * the signer's signature over its signed attributes (RSA PKCS#1 v1.5 and ECDSA through WebCrypto),
 * the signer certificate and whether the file was changed after signing. The certificate chain is
 * not checked against a trust list in this beta.
 */
(function (global) {
  'use strict';

  const latin1 = new TextDecoder('latin1');
  const enc = s => { const out = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i) & 255; return out; };
  const concat = parts => { const n = parts.reduce((a, p) => a + p.length, 0), out = new Uint8Array(n); let o = 0; for (const p of parts) { out.set(p, o); o += p.length; } return out; };
  const binary = bytes => { let s = ''; for (let i = 0; i < bytes.length; i += 32768) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 32768)); return s; };
  const pad = (n, w) => String(n).padStart(w, '0');

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
    if (!key) throw new Error('No private key in the certificate file (only RSA keys are supported in this beta).');
    if (!certs.length) throw new Error('No certificate in the certificate file.');
    const cert = certs.find(c => c.publicKey && c.publicKey.n && c.publicKey.n.equals(key.n)) || certs[0];
    return { key, cert, chain: certs, subject: (cert.subject.getField('CN') || {}).value || '', notAfter: cert.validity.notAfter };
  }

  // ---------------------------------------------------------------------------------------------
  // Signing (incremental update)

  async function signPdf(bytes, options) {
    const PDFLib = global.PDFLib, forge = global.forge;
    const { PDFName, PDFArray, PDFDict, PDFRef, PDFHexString, PDFNumber } = PDFLib;
    const o = Object.assign({ reason: '', location: '', contact: '', pageIndex: 0, placeholderBytes: 12000, now: new Date() }, options);
    const certificate = readCertificate(o.p12, o.password);
    let doc;
    try { doc = await PDFLib.PDFDocument.load(bytes, { updateMetadata: false }); } catch (e) {
      throw new Error(/encrypt/i.test(String(e && e.message)) ? 'Encrypted PDFs cannot be signed in this beta.' : 'The PDF could not be read: ' + (e && e.message));
    }
    const ctx = doc.context, text = latin1.decode(bytes);
    const prev = lastStartXref(text), classic = text.slice(prev, prev + 4) === 'xref';
    const catalogRef = ctx.trailerInfo.Root, infoRef = ctx.trailerInfo.Info, id = ctx.trailerInfo.ID;
    const page = doc.getPage(Math.min(Math.max(0, o.pageIndex | 0), doc.getPageCount() - 1));
    let next = ctx.largestObjectNumber + 1;
    const sigNum = next++, widgetNum = next++, widgetRef = PDFRef.of(widgetNum), sigRef = PDFRef.of(sigNum);
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
    if (afEntry instanceof PDFRef) {
      rewritten.push([afEntry.objectNumber, withField(ctx.lookup(afEntry).clone(ctx)).toString()]);
    } else {
      const cat = doc.catalog.clone(ctx);
      cat.set(PDFName.of('AcroForm'), withField(afEntry instanceof PDFDict ? afEntry.clone(ctx) : ctx.obj({})));
      rewritten.push([catalogRef.objectNumber, cat.toString()]);
    }

    const hexText = s => PDFHexString.fromText(String(s)).toString();
    const contentsLen = o.placeholderBytes * 2, brPlaceholder = '[0 0000000000 0000000000 0000000000]';
    const sigDict = '<< /Type /Sig /Filter /Adobe.PPKLite /SubFilter /adbe.pkcs7.detached /ByteRange ' + brPlaceholder +
      ' /Contents <' + '0'.repeat(contentsLen) + '> /M (' + pdfDate(o.now) + ') /Name ' + hexText(certificate.subject) +
      (o.reason ? ' /Reason ' + hexText(o.reason) : '') + (o.location ? ' /Location ' + hexText(o.location) : '') +
      (o.contact ? ' /ContactInfo ' + hexText(o.contact) : '') + ' >>';
    const widget = '<< /Type /Annot /Subtype /Widget /FT /Sig /T ' + hexText('Signature' + (fieldCount + 1)) + ' /V ' + sigRef + ' /F 132 /Rect [0 0 0 0] /P ' + page.ref + ' >>';
    const objects = [[sigNum, sigDict], [widgetNum, widget], ...rewritten].sort((a, b) => a[0] - b[0]);

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
    const p7 = forge.pkcs7.createSignedData();
    p7.content = forge.util.createBuffer(binary(signed));
    for (const c of certificate.chain) p7.addCertificate(c);
    p7.addSigner({
      key: certificate.key, certificate: certificate.cert, digestAlgorithm: forge.pki.oids.sha256,
      authenticatedAttributes: [{ type: forge.pki.oids.contentType, value: forge.pki.oids.data }, { type: forge.pki.oids.messageDigest }, { type: forge.pki.oids.signingTime, value: o.now }]
    });
    p7.sign({ detached: true });
    const hex = forge.util.bytesToHex(forge.asn1.toDer(p7.toAsn1()).getBytes());
    if (hex.length > contentsLen) throw new Error('The signature is larger than its reserved space.');
    out.set(enc(hex.padEnd(contentsLen, '0')), cStart + 1);
    return { bytes: out, signer: certificate.subject, notAfter: certificate.notAfter };
  }

  // ---------------------------------------------------------------------------------------------
  // Checking existing signatures

  const OID = {
    sha1: '1.3.14.3.2.26', sha256: '2.16.840.1.101.3.4.2.1', sha384: '2.16.840.1.101.3.4.2.2', sha512: '2.16.840.1.101.3.4.2.3',
    messageDigest: '1.2.840.113549.1.9.4', signingTime: '1.2.840.113549.1.9.5', rsa: '1.2.840.113549.1.1.1', ec: '1.2.840.10045.2.1',
    p256: '1.2.840.10045.3.1.7', p384: '1.3.132.0.34', p521: '1.3.132.0.35', commonName: '2.5.4.3'
  };
  const HASH = { [OID.sha1]: 'SHA-1', [OID.sha256]: 'SHA-256', [OID.sha384]: 'SHA-384', [OID.sha512]: 'SHA-512' };

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
        name: str('Name'), reason: str('Reason'), location: str('Location'), time: str('M') });
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
    const forge = global.forge, tbs = certAsn1.value[0], f = tbs.value.slice(tbs.value[0].tagClass === forge.asn1.Class.CONTEXT_SPECIFIC ? 1 : 0);
    const name = n => { for (const rdn of n.value) for (const at of rdn.value) if (forge.asn1.derToOid(at.value[0].value) === OID.commonName) return String(at.value[1].value); return ''; };
    const time = t => (t.type === forge.asn1.Type.UTCTIME ? forge.asn1.utcTimeToDate : forge.asn1.generalizedTimeToDate)(t.value);
    return { serial: forge.util.bytesToHex(f[0].value), issuer: name(f[2]), notBefore: time(f[3].value[0]), notAfter: time(f[3].value[1]), subject: name(f[4]), spki: f[5] };
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
    const forge = global.forge, results = [];
    for (const f of signatureFields(bytes)) {
      const r = { name: f.name, reason: f.reason, location: f.location, time: f.time, subFilter: f.subFilter, coversWholeFile: f.range[2] + f.range[3] === bytes.length, problems: [] };
      try {
        const [a, b, c, d] = f.range;
        if (a !== 0 || c + d > bytes.length || b > c) throw new Error('Invalid byte range.');
        const signed = concat([bytes.subarray(a, a + b), bytes.subarray(c, c + d)]);
        const der = forge.util.hexToBytes(f.contents);
        const ci = forge.asn1.fromDer(der, { parseAllBytes: false, strict: false });
        const sd = ci.value[1].value[0], parts = sd.value;
        const certSet = parts.find(p => p.tagClass === forge.asn1.Class.CONTEXT_SPECIFIC && p.type === 0);
        const signerInfo = parts[parts.length - 1].value[0], si = signerInfo.value;
        const certs = certSet ? certSet.value.map(certInfo) : [];
        const sid = si[1], serial = sid.value && sid.value[1] ? forge.util.bytesToHex(sid.value[1].value) : '';
        const cert = certs.find(x => x.serial === serial) || certs[0];
        const hashName = HASH[forge.asn1.derToOid(si[2].value[0].value)];
        if (!hashName) throw new Error('Unsupported digest algorithm.');
        let i = 3, attrs = null;
        if (si[i].tagClass === forge.asn1.Class.CONTEXT_SPECIFIC && si[i].type === 0) attrs = si[i++];
        i++; // signature algorithm
        const sig = enc(si[i].value), docHash = await digest(hashName, signed);
        if (attrs) {
          const md = attrs.value.find(at => forge.asn1.derToOid(at.value[0].value) === OID.messageDigest);
          r.integrity = !!md && same(enc(md.value[1].value[0].value), docHash);
          const st = attrs.value.find(at => forge.asn1.derToOid(at.value[0].value) === OID.signingTime);
          if (st) { const t = st.value[1].value[0]; r.signedAt = (t.type === forge.asn1.Type.UTCTIME ? forge.asn1.utcTimeToDate : forge.asn1.generalizedTimeToDate)(t.value); }
          const setDer = forge.asn1.toDer(forge.asn1.create(forge.asn1.Class.UNIVERSAL, forge.asn1.Type.SET, true, attrs.value)).getBytes();
          r.signatureValid = cert ? await verifySignature(cert.spki, hashName, enc(setDer), sig) : null;
        } else {
          r.integrity = null;
          r.signatureValid = cert ? await verifySignature(cert.spki, hashName, signed, sig) : null;
        }
        if (cert) {
          Object.assign(r, { signer: cert.subject, issuer: cert.issuer, notBefore: cert.notBefore, notAfter: cert.notAfter });
          const when = r.signedAt || new Date();
          r.certificateValidAtSigning = when >= cert.notBefore && when <= cert.notAfter;
        } else r.problems.push('No signer certificate in the signature.');
        if (r.signatureValid === null) r.problems.push('Signature algorithm not supported by this check.');
        r.ok = r.integrity !== false && r.signatureValid === true;
      } catch (e) {
        r.ok = false; r.problems.push(String(e && e.message || e));
      }
      results.push(r);
    }
    return results;
  }

  global.InkDOSPdfLabSign = Object.freeze({ signPdf, checkPdf, readCertificate, _test: { signatureFields, decodePdfString } });
})(globalThis);
