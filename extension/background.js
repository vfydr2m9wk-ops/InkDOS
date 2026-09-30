// InkDOS browser extension: a thin compatibility layer over the hosted InkDOS web apps.
// It opens InkDOS, and opens files behind links (including Google Drive / Docs) in the matching
// workspace: the file is downloaded with the browser's own session and handed to the workspace page.
'use strict';
const INKDOS = 'https://vfydr2m9wk-ops.github.io/InkDOS/';
const MAX_BYTES = 40 * 1024 * 1024;
// Same routing as Home (assets/home-launch.js).
const ROUTES = [
  {app: 'documents', ext: ['docx', 'rtf', 'doc'], mime: ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/rtf', 'application/msword']},
  {app: 'spreadsheets', ext: ['xlsx', 'xls', 'csv', 'tsv'], mime: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel', 'text/csv', 'text/tab-separated-values']},
  {app: 'presentations', ext: ['pptx', 'ppt'], mime: ['application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.ms-powerpoint']},
  {app: 'pdf', ext: ['pdf'], mime: ['application/pdf']},
  {app: 'epub', ext: ['epub'], mime: ['application/epub+zip']},
  {app: 'txt', ext: ['txt', 'md', 'markdown', 'log', 'ini', 'cfg', 'conf', 'toml', 'properties', 'xml', 'json', 'jsonl', 'ndjson', 'yaml', 'yml'], mime: ['text/plain', 'application/xml', 'application/json', 'application/yaml']}
];
const EXT_BY_MIME = new Map(ROUTES.flatMap(r => r.mime.map((m, i) => [m, r.ext[Math.min(i, r.ext.length - 1)]])));
const LINK_PATTERNS = [
  ...ROUTES.flatMap(r => r.ext).flatMap(e => [`*://*/*.${e}`, `*://*/*.${e}?*`, `*://*/*.${e}#*`]),
  '*://drive.google.com/*', '*://drive.usercontent.google.com/*', '*://docs.google.com/*'
];
const CLOUD_PAGES = ['*://drive.google.com/file/d/*', '*://docs.google.com/document/d/*', '*://docs.google.com/spreadsheets/d/*', '*://docs.google.com/presentation/d/*'];
const pending = new Map();

function routeFor(name, type) {
  const dot = name.lastIndexOf('.'), ext = dot >= 0 ? name.slice(dot + 1).toLowerCase() : '';
  type = String(type || '').split(';')[0].trim().toLowerCase();
  return ROUTES.find(r => ext && r.ext.includes(ext)) || ROUTES.find(r => type && r.mime.includes(type)) || null;
}

// Google Drive file pages and Google Docs editors become direct downloads (Docs/Sheets/Slides as DOCX/XLSX/PPTX).
function downloadUrl(raw) {
  let url;
  try { url = new URL(raw); } catch (_) { return raw; }
  const id = (/\/d\/([A-Za-z0-9_-]{10,})/.exec(url.pathname) || [])[1] || url.searchParams.get('id');
  if (url.hostname === 'drive.google.com' && id) return `https://drive.usercontent.google.com/download?id=${encodeURIComponent(id)}&export=download&confirm=t`;
  if (url.hostname === 'docs.google.com' && id) {
    if (url.pathname.startsWith('/document/')) return `https://docs.google.com/document/d/${id}/export?format=docx`;
    if (url.pathname.startsWith('/spreadsheets/')) return `https://docs.google.com/spreadsheets/d/${id}/export?format=xlsx`;
    if (url.pathname.startsWith('/presentation/')) return `https://docs.google.com/presentation/d/${id}/export/pptx`;
  }
  return raw;
}

function fileName(response, url, type) {
  const cd = response.headers.get('content-disposition') || '';
  let name = '';
  const star = /filename\*\s*=\s*(?:UTF-8'')?([^;]+)/i.exec(cd), plain = /filename\s*=\s*"?([^";]+)"?/i.exec(cd);
  try { name = star ? decodeURIComponent(star[1].trim().replace(/^"|"$/g, '')) : plain ? plain[1].trim() : ''; } catch (_) { name = plain ? plain[1].trim() : ''; }
  if (!name) { try { name = decodeURIComponent(new URL(url).pathname.split('/').pop() || ''); } catch (_) { name = ''; } }
  if (!name || !name.includes('.')) { const ext = EXT_BY_MIME.get(String(type).split(';')[0].trim().toLowerCase()); name = (name || 'document') + (ext ? '.' + ext : ''); }
  return name;
}

function base64(buffer) {
  const bytes = new Uint8Array(buffer); let out = '';
  for (let i = 0; i < bytes.length; i += 0x8000) out += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(out);
}

async function fail(message) {
  console.warn('InkDOS:', message);
  try { await chrome.action.setBadgeText({text: '!'}); await chrome.action.setBadgeBackgroundColor({color: '#b42318'}); await chrome.action.setTitle({title: 'InkDOS: ' + message}); } catch (_) {}
}

// Downloads the file behind a link with the browser's session and returns the workspace URL that receives it.
async function prepare(raw) {
  const url = downloadUrl(raw);
  try { await chrome.action.setBadgeText({text: ''}); await chrome.action.setTitle({title: 'Open InkDOS'}); } catch (_) {}
  let response;
  try { response = await fetch(url, {credentials: 'include', redirect: 'follow'}); } catch (e) { throw new Error('could not download the file (' + (e.message || e) + ')'); }
  if (!response.ok) throw new Error(`the server answered ${response.status}; sign in to the site or check that the link can be opened`);
  const type = response.headers.get('content-type') || '', name = fileName(response, response.url || url, type), route = routeFor(name, type);
  if (!route) throw new Error(`"${name}" is not a format InkDOS opens`);
  if (/text\/html/i.test(type) && route.app !== 'txt') throw new Error('the link returned a web page instead of the file (sign in, or open the file page and try again)');
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength > MAX_BYTES) throw new Error('the file is larger than 40 MB');
  const token = crypto.randomUUID();
  pending.set(token, {name, type: type.split(';')[0].trim(), data: base64(buffer)});
  setTimeout(() => pending.delete(token), 120000);
  return `${INKDOS}apps/${route.app}/index.html#inkdos-ext=${token}`;
}

async function openLink(raw) {
  let target;
  try { target = await prepare(raw); } catch (e) { return fail(e.message || String(e)); }
  await chrome.tabs.create({url: target});
}

// Optional behaviors (options page): open PDFs in InkDOS instead of the browser's PDF viewer, and open downloaded
// documents in InkDOS instead of saving them. Both are on by default and can be turned off.
const DEFAULTS = {pdfViewer: true, downloads: true};
const VIEWER_RULE = 1;
async function settings() { return {...DEFAULTS, ...(await chrome.storage.local.get(Object.keys(DEFAULTS)))}; }

// A PDF opened in a tab is redirected, before the viewer loads, to open.html, which hands it to the PDF workspace.
async function applyViewerRule() {
  const {pdfViewer} = await settings();
  await chrome.declarativeNetRequest.updateDynamicRules({removeRuleIds: [VIEWER_RULE], addRules: pdfViewer ? [{
    id: VIEWER_RULE, priority: 1,
    action: {type: 'redirect', redirect: {regexSubstitution: chrome.runtime.getURL('open.html') + '#\\0'}},
    condition: {regexFilter: '^https?://.*', resourceTypes: ['main_frame'], requestMethods: ['get'],
                excludedRequestDomains: [new URL(INKDOS).hostname],
                responseHeaders: [{header: 'content-type', values: ['application/pdf', 'application/pdf;*', 'application/pdf *']}]}
  }] : []});
}

// "Open in the browser instead": the next load of that exact URL skips the redirect.
async function allowOnce(url) {
  const id = 1000 + Math.floor(Math.random() * 1e6);
  await chrome.declarativeNetRequest.updateSessionRules({addRules: [{id, priority: 2, action: {type: 'allow'},
    condition: {urlFilter: '|' + url + '|', resourceTypes: ['main_frame']}}]});
  setTimeout(() => chrome.declarativeNetRequest.updateSessionRules({removeRuleIds: [id]}).catch(() => {}), 60000);
}

// A download of a document, spreadsheet, presentation, PDF or EPUB opens in InkDOS instead of being saved.
// Plain text/data files, files from blob:/data: URLs (including InkDOS's own Save) and large files download as usual.
// The download is paused while its name and type are checked; a generic type is checked from the response headers only.
const GENERIC = /^(|application\/(octet-stream|force-download|x-download|binary|unknown)|binary\/.*)$/i;
async function probe(url) {
  const abort = new AbortController();
  try {
    const response = await fetch(downloadUrl(url), {credentials: 'include', redirect: 'follow', signal: abort.signal});
    const type = response.headers.get('content-type') || '';
    return {ok: response.ok, name: fileName(response, response.url || url, type), type, size: Number(response.headers.get('content-length')) || 0};
  } finally { abort.abort(); }
}

async function interceptDownload(item) {
  const url = item.finalUrl || item.url || '';
  if (!/^https?:/i.test(url) || url.startsWith(INKDOS) || item.byExtensionId === chrome.runtime.id) return;
  if (!(await settings()).downloads) return;
  const pathName = (() => { try { return decodeURIComponent(new URL(url).pathname.split('/').pop() || ''); } catch (_) { return ''; } })();
  let route = routeFor(String(item.filename || '').split(/[\\/]/).pop() || pathName, item.mime), size = item.totalBytes || item.fileSize || 0;
  let paused = false;
  if (!route && GENERIC.test(String(item.mime || '').split(';')[0].trim())) {
    try { await chrome.downloads.pause(item.id); paused = true; } catch (_) {}
    try { const head = await probe(url); if (head.ok) { route = routeFor(head.name, head.type); size = size || head.size; } } catch (_) {}
  }
  if (!route || route.app === 'txt' || size > MAX_BYTES) { if (paused) chrome.downloads.resume(item.id).catch(() => {}); return; }
  try { await chrome.downloads.cancel(item.id); await chrome.downloads.erase({id: item.id}); } catch (_) {}
  try { await chrome.tabs.create({url: await prepare(url)}); }
  catch (e) { chrome.downloads.download({url}); fail(e.message || String(e)); }
}
chrome.downloads.onCreated.addListener(item => { interceptDownload(item).catch(e => console.warn('InkDOS:', e)); });

chrome.runtime.onStartup.addListener(() => { applyViewerRule().catch(e => console.warn('InkDOS:', e)); });
chrome.storage.onChanged.addListener(changes => { if ('pdfViewer' in changes) applyViewerRule().catch(e => console.warn('InkDOS:', e)); });

chrome.runtime.onInstalled.addListener(() => {
  applyViewerRule().catch(e => console.warn('InkDOS:', e));
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({id: 'inkdos-open-link', title: 'Open with InkDOS', contexts: ['link'], targetUrlPatterns: LINK_PATTERNS});
    chrome.contextMenus.create({id: 'inkdos-open-page', title: 'Open this file in InkDOS', contexts: ['page'], documentUrlPatterns: CLOUD_PAGES});
  });
});

chrome.contextMenus.onClicked.addListener(info => {
  if (info.menuItemId === 'inkdos-open-link' && info.linkUrl) openLink(info.linkUrl);
  else if (info.menuItemId === 'inkdos-open-page' && info.pageUrl) openLink(info.pageUrl);
});

chrome.action.onClicked.addListener(() => chrome.tabs.create({url: INKDOS}));

// The bridge content script on the workspace page asks for the file it was opened for (one time only);
// open.html asks to open a redirected PDF, or to show it in the browser instead.
chrome.runtime.onMessage.addListener((message, sender, reply) => {
  if (message?.type === 'inkdos-open-url' && sender.url?.startsWith(chrome.runtime.getURL('open.html'))) {
    prepare(message.url).then(url => reply({url}), e => reply({error: e.message || String(e)}));
    return true;
  }
  if (message?.type === 'inkdos-allow-once' && sender.url?.startsWith(chrome.runtime.getURL('open.html'))) {
    allowOnce(message.url).then(() => reply({ok: true}), e => reply({error: String(e)}));
    return true;
  }
  if (message?.type !== 'inkdos-ext-file' || !sender.tab || !String(sender.url || '').startsWith(INKDOS)) return false;
  const file = pending.get(message.token);
  pending.delete(message.token);
  reply(file || {error: 'expired'});
  return false;
});
