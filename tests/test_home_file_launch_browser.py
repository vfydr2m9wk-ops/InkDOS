#!/usr/bin/env python3
"""Home declares every supported format and sends each launched file straight to its workspace.

Each Home file handler targets the workspace page itself, so a host that honours handler actions
opens the workspace directly (its own launchQueue bridge loads the file). Hosts that deliver the
launch to Home instead are covered by Home's fallback router, tested below.

Hosts such as XeOS group every InkDOS page under one app, so Home is the file entry point:
it must declare all workspace formats, route each launched file to the right workspace
(loaded unchanged in a frame) and keep earlier files open when another file arrives.
"""
from __future__ import annotations
import base64, io, json, os, socket, subprocess, sys, time, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"
APPS = ["documents", "spreadsheets", "presentations", "pdf", "txt", "epub"]

LAUNCH_STUB = r"""(() => {
  let consumer = null; const pending = [];
  window.__inkdosLaunch = (files) => { const p = { files: files.map(f => ({ kind: 'file', getFile: async () => f })) }; if (consumer) consumer(p); else pending.push(p); };
  Object.defineProperty(window, 'launchQueue', { configurable: true, value: { setConsumer(fn) { consumer = fn; while (pending.length) fn(pending.shift()); } } });
})();"""


def docx_bytes() -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Home launch document</w:t></w:r></w:p></w:body></w:document>')
    return out.getvalue()


def pdf_bytes() -> bytes:
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    stream = b"BT /F1 24 Tf 72 700 Td (Home launch PDF) Tj ET"
    out = io.BytesIO(); out.write(b"%PDF-1.4\n"); offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(out.tell())
        if body is None:
            out.write(f"{i} 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream\nendobj\n")
        else:
            out.write(f"{i} 0 obj\n{body}\nendobj\n".encode())
    xref = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def epub_bytes() -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf", '<?xml version="1.0" encoding="UTF-8"?><package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">home-launch</dc:identifier><dc:title>Home Launch</dc:title><dc:language>en</dc:language></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="c1" href="c1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>')
        z.writestr("OEBPS/nav.xhtml", '<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Nav</title></head><body><nav epub:type="toc"><ol><li><a href="c1.xhtml">One</a></li></ol></nav></body></html>')
        z.writestr("OEBPS/c1.xhtml", '<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>One</title></head><body><p>Home launch book</p></body></html>')
    return out.getvalue()


CASES = [
    ("launch.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", docx_bytes, "documents",
     "d => !!d.defaultView.InkDOS2Documents?.DocumentsApp?.session && d.body.innerText.includes('Home launch document')"),
    ("launch.csv", "text/csv", lambda: b"Name,Value\nHome launch,42\n", "spreadsheets",
     "d => d.getElementById('startState')?.hidden === true && !!d.defaultView.__inkdosSpreadsheetsS1?.session?.book?.loaded"),
    ("launch.pdf", "application/pdf", pdf_bytes, "pdf",
     "d => d.defaultView.InkDOS2PdfP4?.PdfStabilityDebug?.layout?.pageCount === 1 && !!d.querySelector('canvas')"),
    ("launch.md", "text/markdown", lambda: b"# Home launch text\n", "txt",
     "d => (d.getElementById('editor')?.value || '').includes('Home launch text')"),
    ("launch.epub", "application/epub+zip", epub_bytes, "epub",
     "d => d.getElementById('emptyState')?.hidden === true"),
]


def wait_port():
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(.2)
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(.1)
    raise RuntimeError("Local test server did not start")


def check_manifest():
    home = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    handlers = {h.get("action"): h["accept"] for h in home.get("file_handlers", [])}
    for app in APPS:
        action = f"./apps/{app}/index.html"
        assert action in handlers, f"Home must launch {app} files straight into the {app} workspace ({action})"
        m = json.loads((ROOT / "apps" / app / "manifest.webmanifest").read_text(encoding="utf-8"))
        for h in m.get("file_handlers", []):
            for mime, exts in h["accept"].items():
                missing = set(exts) - set(handlers[action].get(mime, []))
                assert not missing, f"Home must accept every {app} format: {mime} {sorted(missing)}"
    assert (home.get("launch_handler") or {}).get("client_mode") == "navigate-new", "each launched file should get its own window"


def main():
    check_manifest()
    browser_name = os.environ.get("BROWSER", "chromium")
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_port()
        with sync_playwright() as pw:
            args = {"headless": True}
            if os.environ.get("CHROMIUM_PATH") and browser_name == "chromium":
                args["executable_path"] = os.environ["CHROMIUM_PATH"]
            browser = getattr(pw, browser_name).launch(**args)
            # Routing covers every declared extension, including formats without a fixture here.
            page = browser.new_page()
            page.goto(BASE + "/index.html", wait_until="load")
            routes = page.evaluate("() => globalThis.InkDOSHomeLaunch.routes")
            expected = {}
            for app in APPS:
                m = json.loads((ROOT / "apps" / app / "manifest.webmanifest").read_text(encoding="utf-8"))
                for h in m.get("file_handlers", []):
                    for exts in h["accept"].values():
                        for e in exts:
                            expected[e.lstrip(".")] = app
            got = {e: r["app"] for r in routes for e in r["ext"]}
            assert got == expected, {"missing_or_wrong": {k: (v, got.get(k)) for k, v in expected.items() if got.get(k) != v}}
            page.close()

            for name, mime, make, app, ready in CASES:
                ctx = browser.new_context(viewport={"width": 1280, "height": 860}, service_workers="block")
                ctx.add_init_script(LAUNCH_STUB)
                page = ctx.new_page()
                page.goto(BASE + "/index.html", wait_until="load")
                data = base64.b64encode(make()).decode()
                page.evaluate("([n, t, b]) => { const raw = atob(b), u = new Uint8Array(raw.length); for (let i = 0; i < raw.length; i++) u[i] = raw.charCodeAt(i); window.__inkdosLaunch([new File([u], n, {type: t})]); }", [name, mime, data])
                page.wait_for_function(f"() => {{ const f = document.querySelector('.home-launch-frame:not([hidden])'); return !!f && f.getAttribute('src') === './apps/{app}/index.html'; }}", timeout=15000)
                page.wait_for_function(f"() => {{ const d = document.querySelector('.home-launch-frame:not([hidden])')?.contentDocument; try {{ return !!d && ({ready})(d); }} catch (_) {{ return false; }} }}", timeout=30000)
                assert page.evaluate("() => document.body.classList.contains('home-launching')")
                ctx.close()
                print(f"  {name} -> {app}: OK")

            # A second file arriving in the same window keeps the first one open (tabs).
            ctx = browser.new_context(viewport={"width": 1280, "height": 860}, service_workers="block")
            ctx.add_init_script(LAUNCH_STUB)
            page = ctx.new_page()
            page.goto(BASE + "/index.html", wait_until="load")
            for name, mime, make, app, ready in (CASES[2], CASES[0]):
                data = base64.b64encode(make()).decode()
                page.evaluate("([n, t, b]) => { const raw = atob(b), u = new Uint8Array(raw.length); for (let i = 0; i < raw.length; i++) u[i] = raw.charCodeAt(i); window.__inkdosLaunch([new File([u], n, {type: t})]); }", [name, mime, data])
                page.wait_for_function(f"() => {{ const d = document.querySelector('.home-launch-frame:not([hidden])')?.contentDocument; try {{ return !!d && ({ready})(d); }} catch (_) {{ return false; }} }}", timeout=30000)
            state = page.evaluate("() => ({frames: [...document.querySelectorAll('.home-launch-frame')].map(f => f.getAttribute('src')), tabs: document.querySelectorAll('.home-launch-tab').length, barHidden: document.querySelector('.home-launch-tabs').hidden})")
            assert state == {"frames": ["./apps/pdf/index.html", "./apps/documents/index.html"], "tabs": 2, "barHidden": False}, state
            page.click(".home-launch-tab >> nth=0")
            page.wait_for_function("() => document.querySelector('.home-launch-frame:not([hidden])')?.getAttribute('src') === './apps/pdf/index.html'")
            ctx.close()
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"Home file launch routing ({browser_name}): OK")


if __name__ == "__main__":
    main()
