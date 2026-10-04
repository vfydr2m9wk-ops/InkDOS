/* InkDOS PDF Lab (beta): page wiring. One working document; every tool reads it and its result
 * becomes the new working document, so tools can be chained (OCR, then visual, then digital). */
(function () {
  'use strict';

  const $ = id => document.getElementById(id);
  const PT = /^pt/i.test(navigator.language || '');
  const T = PT ? {
    back: '← InkDOS', title: 'Ferramentas de PDF', intro: 'Ferramentas experimentais da versão web. Tudo roda neste navegador: arquivos, certificados e senhas não saem do seu dispositivo.',
    open: 'Abrir PDF', noFile: 'Nenhum PDF aberto', download: 'Baixar resultado', tabOcr: 'OCR (texto pesquisável)', tabStamp: 'Assinatura visual',
    tabSign: 'Assinatura digital (A1)', tabCheck: 'Verificar assinaturas',
    ocrHelp: 'Reconhece o texto de páginas escaneadas e adiciona uma camada de texto invisível, para o PDF poder ser pesquisado e copiado. As páginas continuam iguais.',
    language: 'Idioma', ocrAll: 'Também páginas que já têm texto', ocrRun: 'Executar OCR',
    stampHelp: 'Desenhe ou escolha uma imagem de assinatura e clique na página onde ela fica. A assinatura visual é uma imagem: para validade jurídica use a assinatura digital.',
    clear: 'Limpar', chooseImage: 'Usar uma imagem…', page: 'Página', size: 'Largura', stampRun: 'Colocar assinatura',
    signHelp: 'Assina o PDF no padrão PAdES com seu certificado A1 (.pfx/.p12) válido. A assinatura é acrescentada ao arquivo, então assinaturas anteriores continuam válidas. Coloque a assinatura visual antes.',
    signVisible: 'Mostrar a assinatura com data e hora na página', position: 'Posição', posBL: 'Rodapé à esquerda', posBR: 'Rodapé à direita', posTR: 'Topo à direita',
    signLock: 'Bloquear o documento após assinar', signLockHelp: 'Bloquear certifica o documento: qualquer alteração posterior (texto, páginas, anotações ou outra assinatura) faz os leitores de PDF indicarem a assinatura como inválida. Só a primeira assinatura pode bloquear um documento.',
    signedBy: 'Assinado digitalmente por', dateLabel: 'Data', locked: 'Documento bloqueado (certificado): alterações posteriores não são permitidas.',
    certificate: 'Certificado (.pfx/.p12)', password: 'Senha', reason: 'Motivo', location: 'Local', signRun: 'Assinar PDF',
    checkHelp: 'Confere se cada assinatura corresponde ao documento e se o documento não foi alterado depois. A cadeia do certificado é mostrada, mas nesta versão beta não é conferida contra uma lista de autoridades confiáveis.',
    checkRun: 'Verificar assinaturas', returnApp: 'Abrir no InkDOS', returned: 'Resultado aberto no app do InkDOS.', needPdf: 'Abra um PDF primeiro.', opened: 'PDF aberto', ocrLoading: 'Carregando o OCR…',
    ocrPage: (d, t) => `Reconhecendo páginas: ${d} de ${t}`, ocrWriting: 'Gravando o texto…',
    ocrDone: (p, w, s) => `OCR concluído: ${p} página(s), ${w} palavras${s ? `; ${s} página(s) já tinham texto` : ''}.`, ocrNothing: 'Todas as páginas já têm texto; nada a fazer.',
    stampNeed: 'Desenhe ou escolha a assinatura e clique na página para posicioná-la.', stampDone: 'Assinatura visual colocada.',
    stampSigned: 'Este PDF já tem assinatura digital: colocar uma imagem agora invalidaria a assinatura.',
    signNeed: 'Escolha o certificado.', signing: 'Assinando…', signDone: n => `Assinado por ${n}.`,
    checking: 'Verificando…', none: 'Nenhuma assinatura digital neste PDF.', valid: 'Assinatura íntegra · identidade não verificada', untrusted: 'O documento não mudou desde a assinatura, mas esta versão beta não confirma se o certificado foi emitido por uma autoridade confiável (ICP-Brasil ou outra). Confira o emissor ou valide no verificador oficial (validar.iti.gov.br).', invalid: 'Assinatura inválida',
    changedAfter: 'O documento recebeu alterações depois desta assinatura.', wholeFile: 'Cobre o documento inteiro.',
    signer: 'Assinante', issuer: 'Emissor', signedAt: 'Assinado em', certExpired: 'O certificado não era válido na data da assinatura.', reasonL: 'Motivo',
    chain: 'Cadeia', notes: {
      'no-timestamp': 'Sem carimbo do tempo: a data da assinatura é a do relógio do computador de quem assinou.',
      'timestamp-not-checked': 'Há um carimbo do tempo, mas esta versão beta não o confere.',
      'chain-incomplete': 'A cadeia do certificado está incompleta dentro da assinatura.',
      'chain-unsupported': 'A cadeia do certificado usa um algoritmo que esta verificação não confere.',
      'weak-chain-hash': 'A cadeia do certificado usa SHA-1, considerado fraco.',
      'weak-key': 'A chave do certificado tem menos de 2048 bits, considerada fraca.',
      'no-signing-certificate': 'A assinatura não vincula o certificado nos atributos assinados (não é PAdES).'
    }
  } : {
    returned: 'Result opened in the InkDOS workspace.', needPdf: 'Open a PDF first.', opened: 'PDF opened', ocrLoading: 'Loading OCR…', ocrPage: (d, t) => `Recognising pages: ${d} of ${t}`, ocrWriting: 'Writing the text…',
    ocrDone: (p, w, s) => `OCR finished: ${p} page(s), ${w} words${s ? `; ${s} page(s) already had text` : ''}.`, ocrNothing: 'Every page already has text; nothing to do.',
    stampNeed: 'Draw or choose the signature and click on the page to place it.', stampDone: 'Visual signature placed.',
    stampSigned: 'This PDF is already digitally signed: adding a picture now would invalidate the signature.',
    signedBy: 'Digitally signed by', dateLabel: 'Date', locked: 'Document locked (certified): no later changes are allowed.',
    signNeed: 'Choose the certificate.', signing: 'Signing…', signDone: n => `Signed by ${n}.`, checking: 'Checking…', none: 'No digital signature in this PDF.',
    valid: 'Signature intact · identity not verified', untrusted: 'The document has not changed since signing, but this beta does not confirm that the certificate was issued by a trusted authority. Check the issuer or use an official validator.', invalid: 'Invalid signature', changedAfter: 'The document was changed after this signature.', wholeFile: 'Covers the whole document.',
    signer: 'Signer', issuer: 'Issuer', signedAt: 'Signed at', certExpired: 'The certificate was not valid at signing time.', reasonL: 'Reason',
    chain: 'Chain', notes: {
      'no-timestamp': 'No timestamp: the signing time comes from the signer\'s computer clock.',
      'timestamp-not-checked': 'There is a timestamp, but this beta does not check it.',
      'chain-incomplete': 'The certificate chain inside the signature is incomplete.',
      'chain-unsupported': 'The certificate chain uses an algorithm this check does not verify.',
      'weak-chain-hash': 'The certificate chain uses SHA-1, which is considered weak.',
      'weak-key': 'The certificate key is shorter than 2048 bits, which is considered weak.',
      'no-signing-certificate': 'The signature does not bind its certificate in the signed attributes (not PAdES).'
    }
  };
  if (PT) { document.documentElement.lang = 'pt-BR'; for (const el of document.querySelectorAll('[data-i18n]')) if (typeof T[el.dataset.i18n] === 'string') el.textContent = T[el.dataset.i18n]; document.title = 'InkDOS — ' + T.title + ' (beta)'; }

  pdfjsLib.GlobalWorkerOptions.workerSrc = '../../apps/pdf/vendor/pdfjs/pdf.worker.min.js';
  const doc = { name: '', bytes: null, changed: false };
  const status = (msg, error) => { $('status').textContent = msg || ''; $('status').classList.toggle('error', !!error); };
  const fail = e => { console.error(e); status(String(e && e.message || e), true); };
  const busy = (on) => document.querySelectorAll('.panel .button, #pdfInput').forEach(b => { b.disabled = on; });
  const need = () => { if (!doc.bytes) { status(T.needPdf, true); return false; } return true; };
  const readFile = f => f.arrayBuffer().then(b => new Uint8Array(b));
  const base = () => doc.name.replace(/\.pdf$/i, '');

  // opened from an InkDOS workspace: it hands over its current PDF and takes results back
  const opener = new URLSearchParams(location.search).has('from') && window.opener && !window.opener.closed ? window.opener : null;
  function setResult(bytes, suffix) {
    doc.bytes = bytes; doc.changed = true; doc.suffix = suffix;
    $('downloadBtn').hidden = false; $('returnBtn').hidden = !opener; renderPreview();
  }
  function loadDocument(name, bytes) {
    doc.name = name; doc.bytes = bytes; doc.changed = false;
    $('fileName').textContent = name; $('downloadBtn').hidden = true; $('returnBtn').hidden = true; $('checkList').replaceChildren();
    status(T.opened); renderPreview();
  }

  $('pdfInput').addEventListener('change', async e => {
    const f = e.target.files[0]; if (!f) return;
    loadDocument(f.name, await readFile(f));
  });
  if (opener) {
    window.addEventListener('message', e => {
      if (e.origin !== location.origin || !e.data || e.data.type !== 'inkdos-lab-file') return;
      loadDocument(String(e.data.name || 'document.pdf'), new Uint8Array(e.data.bytes));
    });
    try { opener.postMessage({ type: 'inkdos-lab-ready' }, location.origin); } catch (_) {}
  }
  $('returnBtn').addEventListener('click', () => {
    if (!opener || opener.closed || !doc.bytes) return;
    opener.postMessage({ type: 'inkdos-lab-result', name: base() + (doc.suffix || '') + '.pdf', bytes: doc.bytes }, location.origin);
    try { opener.focus(); } catch (_) {}
    status(T.returned);
  });
  $('downloadBtn').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([doc.bytes], { type: 'application/pdf' })), a = document.createElement('a');
    a.href = url; a.download = base() + (doc.suffix || '') + '.pdf'; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  });

  for (const tab of document.querySelectorAll('[role=tab]')) tab.addEventListener('click', () => {
    for (const t of document.querySelectorAll('[role=tab]')) t.setAttribute('aria-selected', String(t === tab));
    for (const p of document.querySelectorAll('[data-panel]')) p.hidden = p.dataset.panel !== tab.dataset.tab;
    if (tab.dataset.tab === 'stamp') renderPreview();
  });

  // ---- OCR
  $('ocrBtn').addEventListener('click', async () => {
    if (!need()) return;
    const bar = $('ocrProgress'); busy(true); bar.hidden = false; bar.value = 0; status(T.ocrLoading);
    try {
      const r = await InkDOSPdfLabOcr.ocrPdf(doc.bytes, {
        languages: $('ocrLang').value, allPages: $('ocrAll').checked,
        onProgress: p => { if (p.phase === 'recognize') { bar.value = p.done / p.total; status(T.ocrPage(p.done, p.total)); } else if (p.phase === 'write') status(T.ocrWriting); }
      });
      if (!r.pages) status(T.ocrNothing); else { setResult(r.bytes, '-ocr'); status(T.ocrDone(r.pages, r.words, r.skipped)); }
    } catch (e) { fail(e); } finally { busy(false); bar.hidden = true; }
  });

  // ---- visual signature
  const pad = $('pad'), pctx = pad.getContext('2d');
  let drawn = false, image = null, place = null, previewInfo = null;
  pctx.lineWidth = 2.6; pctx.lineCap = pctx.lineJoin = 'round'; pctx.strokeStyle = '#1b2a4a';
  const padPoint = e => { const r = pad.getBoundingClientRect(); return [(e.clientX - r.left) * pad.width / r.width, (e.clientY - r.top) * pad.height / r.height]; };
  pad.addEventListener('pointerdown', e => { pad.setPointerCapture(e.pointerId); const [x, y] = padPoint(e); pctx.beginPath(); pctx.moveTo(x, y); pad.dataset.down = '1'; });
  pad.addEventListener('pointermove', e => { if (!pad.dataset.down) return; const [x, y] = padPoint(e); pctx.lineTo(x, y); pctx.stroke(); drawn = true; image = null; updateMark(); });
  pad.addEventListener('pointerup', () => { delete pad.dataset.down; });
  $('padClear').addEventListener('click', () => { pctx.clearRect(0, 0, pad.width, pad.height); drawn = false; image = null; updateMark(); });
  $('stampImage').addEventListener('change', async e => { const f = e.target.files[0]; if (!f) return; image = { bytes: await readFile(f), type: f.type, url: URL.createObjectURL(f) }; updateMark(); });
  $('stampPage').addEventListener('change', renderPreview);
  $('stampWidth').addEventListener('input', updateMark);
  $('preview').addEventListener('click', e => { const r = e.currentTarget.getBoundingClientRect(); place = { fx: (e.clientX - r.left) / r.width, fy: (e.clientY - r.top) / r.height }; updateMark(); });

  // the drawn signature, cropped to its strokes, as PNG
  function padImage() {
    const d = pctx.getImageData(0, 0, pad.width, pad.height).data; let x0 = pad.width, y0 = pad.height, x1 = 0, y1 = 0;
    for (let y = 0; y < pad.height; y++) for (let x = 0; x < pad.width; x++) if (d[(y * pad.width + x) * 4 + 3] > 0) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    if (x1 <= x0) return null;
    const c = document.createElement('canvas'); c.width = x1 - x0 + 8; c.height = y1 - y0 + 8; c.getContext('2d').drawImage(pad, x0 - 4, y0 - 4, c.width, c.height, 0, 0, c.width, c.height);
    const url = c.toDataURL('image/png'), bin = atob(url.split(',')[1]), bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return { bytes, type: 'image/png', url, ratio: c.height / c.width };
  }
  function currentStamp() { return image || (drawn ? padImage() : null); }

  async function renderPreview() {
    if (!doc.bytes || document.querySelector('[data-panel=stamp]').hidden) return;
    const pdf = await pdfjsLib.getDocument({ data: doc.bytes.slice(), isEvalSupported: false }).promise;
    const n = Math.min(Math.max(1, Number($('stampPage').value) || 1), pdf.numPages); $('stampPage').max = String(pdf.numPages); $('stampPage').value = String(n);
    const page = await pdf.getPage(n), vp = page.getViewport({ scale: 1 }), scale = Math.min(1.5, 760 / vp.width), viewport = page.getViewport({ scale });
    const canvas = $('preview'); canvas.width = viewport.width; canvas.height = viewport.height;
    await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
    previewInfo = { viewport, pageIndex: n - 1 }; await pdf.destroy(); updateMark();
  }

  function updateMark() {
    const mark = $('stampMark'), s = currentStamp();
    if (!place || !s || !previewInfo) { mark.hidden = true; return; }
    const canvas = $('preview'), w = canvas.clientWidth * Number($('stampWidth').value) / 100;
    const ratio = s.ratio || 0.35;
    mark.hidden = false; mark.style.width = w + 'px'; mark.style.height = (w * ratio) + 'px';
    mark.style.left = (place.fx * canvas.clientWidth - w / 2) + 'px'; mark.style.top = (place.fy * canvas.clientHeight - w * ratio / 2) + 'px';
    mark.style.backgroundImage = `url("${s.url}")`;
  }

  $('stampBtn').addEventListener('click', async () => {
    if (!need()) return;
    const s = currentStamp();
    if (!s || !place || !previewInfo) { status(T.stampNeed, true); return; }
    busy(true);
    try {
      if ((await InkDOSPdfLabSign.checkPdf(doc.bytes)).length) { status(T.stampSigned, true); return; }
      const pdf = await PDFLib.PDFDocument.load(doc.bytes, { updateMetadata: false });
      const img = /png/.test(s.type) ? await pdf.embedPng(s.bytes) : await pdf.embedJpg(s.bytes);
      const page = pdf.getPage(previewInfo.pageIndex), vp = previewInfo.viewport;
      const [cx, cy] = vp.convertToPdfPoint(place.fx * vp.width, place.fy * vp.height);
      const pageWidth = Math.abs(vp.convertToPdfPoint(vp.width, 0)[0] - vp.convertToPdfPoint(0, 0)[0]) || page.getWidth();
      const w = pageWidth * Number($('stampWidth').value) / 100, h = w * (img.height / img.width);
      page.drawImage(img, { x: cx - w / 2, y: cy - h / 2, width: w, height: h });
      setResult(await pdf.save(), '-assinado');
      place = null; updateMark(); status(T.stampDone);
    } catch (e) { fail(e); } finally { busy(false); }
  });

  // ---- digital signature
  $('signBtn').addEventListener('click', async () => {
    if (!need()) return;
    const f = $('p12Input').files[0]; if (!f) { status(T.signNeed, true); return; }
    busy(true); status(T.signing);
    try {
      const r = await InkDOSPdfLabSign.signPdf(doc.bytes, { p12: await readFile(f), password: $('p12Password').value, reason: $('signReason').value.trim(), location: $('signLocation').value.trim(),
        pageIndex: Math.max(0, (Number($('signPage').value) || 1) - 1), visible: $('signVisible').checked ? { position: $('signPosition').value } : null, lock: $('signLock').checked,
        labels: { signedBy: T.signedBy, date: T.dateLabel } });
      $('p12Password').value = '';
      setResult(r.bytes, '-assinado'); status(T.signDone(r.signer));
    } catch (e) { fail(e); } finally { busy(false); }
  });

  // ---- check
  $('checkBtn').addEventListener('click', async () => {
    if (!need()) return;
    busy(true); status(T.checking); const list = $('checkList'); list.replaceChildren();
    try {
      const results = await InkDOSPdfLabSign.checkPdf(doc.bytes);
      if (!results.length) { status(T.none); return; }
      const fmt = d => d instanceof Date ? d.toLocaleString() : (d || '');
      results.forEach((r, i) => {
        const li = document.createElement('li'), head = document.createElement('span');
        head.className = r.ok ? 'ok' : 'bad'; head.textContent = `#${i + 1} · ${r.ok ? T.valid : T.invalid}`; li.append(head);
        const lines = [r.signer && `${T.signer}: ${r.signer}`, r.issuer && `${T.issuer}: ${r.issuer}`, r.signedAt && `${T.signedAt}: ${fmt(r.signedAt)}`, r.reason && `${T.reasonL}: ${r.reason}`,
          r.ok && T.untrusted, r.locked && T.locked, r.coversWholeFile ? T.wholeFile : T.changedAfter, r.certificateValidAtSigning === false && T.certExpired, r.chain && r.chain.length && `${T.chain}: ${r.chain.join(' → ')}`, ...r.problems, ...(r.notes || []).map(n => T.notes[n])];
        for (const l of lines.filter(Boolean)) { const s = document.createElement('small'); s.textContent = l; li.append(s); }
        list.append(li);
      });
      status('');
    } catch (e) { fail(e); } finally { busy(false); }
  });
})();
