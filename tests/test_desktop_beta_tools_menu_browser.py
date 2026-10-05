#!/usr/bin/env python3
"""Desktop host: Settings lists the installed beta tools and opens them through the host.

The Tauri bridge (desktop/desktop-host.js) runs against a mocked __TAURI__: the menu shows the
tools of the installed (signed) bundle, a click checks for a newer bundle and then opens the tool
in the host; if the host cannot open it, the user gets the host's error. With a PDF open, the host
gets the PDF with the open request and a result the tool sends back opens in the workspace. Web
behavior (panel) is covered by test_pdf_beta_tools_handoff_browser.py.
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
PORT = 8806
BASE = f"http://127.0.0.1:{PORT}"

MOCK = r"""
window.__mockCalls = [];
window.__mockFailOpen = false;
window.__TAURI__ = {
  dialog: { message: async (text, opts) => { window.__mockCalls.push(['dialog', text]); },
            open: async () => null, save: async () => null },
  fs: { readFile: async () => new Uint8Array(), writeFile: async () => {} },
  opener: {},
  event: { listen: async (name, handler) => { window.__mockListeners = window.__mockListeners || {}; window.__mockListeners[name] = handler; return () => {}; } },
  core: { invoke: async (cmd, args, options) => {
    window.__mockCalls.push([cmd, args instanceof Uint8Array ? { bytes: args.length, pdf: String.fromCharCode(...args.slice(0, 5)), headers: options && options.headers } : (args || null)]);
    if (cmd === 'inkdos_beta_take_result') return new TextEncoder().encode(window.__resultPdf).buffer;
    if (cmd === 'inkdos_beta_status') return { configured: true, installedVersion: 4,
      tools: [{ id: 'pdf', title: 'PDF tools (beta)', entry: 'labs/pdf/index.html' },
              { id: 'scan', title: 'Scanner (beta)', entry: 'labs/scan/index.html' }] };
    if (cmd === 'inkdos_beta_update') throw 'offline';
    if (cmd === 'inkdos_beta_open') { if (window.__mockFailOpen) throw 'Beta tool not found: pdf'; return null; }
    return null;
  } }
};
"""


def one_page_pdf() -> bytes:
    content = b'BT /F1 24 Tf 72 700 Td (Desktop handoff) Tj ET'
    objs = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
            b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n' + content + b'\nendstream',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    out, offsets = bytearray(b'%PDF-1.7\n'), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f'{i} 0 obj\n'.encode() + body + b'\nendobj\n'
    xref = len(out)
    out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n'.encode() + b''.join(f'{o:010d} 00000 n \n'.encode() for o in offsets)
    out += f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    return bytes(out)


PDF = one_page_pdf()


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local test server did not start")


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    errors: list[str] = []
    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(service_workers="block", viewport={"width": 1280, "height": 900})
            context.add_init_script(MOCK)
            page = context.new_page()
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.goto(BASE + "/apps/pdf/index.html", wait_until="load")
            page.add_script_tag(url=BASE + "/desktop/desktop-host.js")
            page.wait_for_function("() => globalThis.InkDOSDesktop?.betaTools?.tools.length === 2")
            page.wait_for_selector('[data-frame-action="sun"]', timeout=15000)

            # the menu lists the installed bundle's tools
            page.click('[data-frame-action="sun"]')
            options = page.eval_on_selector_all(".inkdos-settings-option[data-settings-value^='beta-']",
                                                "els => els.map(e => [e.dataset.settingsValue, e.textContent])")
            assert options == [["beta-pdf", "PDF tools (beta)"], ["beta-scan", "Scanner (beta)"]], options
            page.keyboard.press("Escape")
            page.evaluate("() => { window.__mockCalls = []; }")

            # update check first (offline is tolerated), then open in the host
            page.click('[data-frame-action="sun"]')
            page.click(".inkdos-settings-option[data-settings-value='beta-pdf']")
            page.wait_for_function("() => window.__mockCalls.some(c => c[0] === 'inkdos_beta_open')")
            calls = [c for c in page.evaluate("() => window.__mockCalls") if c[0].startswith("inkdos_beta_") and c[0] != "inkdos_beta_status"]
            assert calls == [["inkdos_beta_update", None], ["inkdos_beta_open", {"tool": "pdf"}]], calls
            assert len(context.pages) == 1, "desktop must not open a browser tab"

            # the host's error reaches the user when it cannot open the tool
            page.evaluate("() => { window.__mockFailOpen = true; window.__mockCalls = []; }")
            page.click('[data-frame-action="sun"]')
            page.click(".inkdos-settings-option[data-settings-value='beta-pdf']")
            page.wait_for_function("() => window.__mockCalls.some(c => c[0] === 'dialog')")
            message = [c for c in page.evaluate("() => window.__mockCalls") if c[0] == "dialog"][0][1]
            assert "Beta tool not found" in message, message

            # with a PDF open, the host gets it with the open request; a result comes back into the workspace
            page.evaluate("() => { window.__mockFailOpen = false; window.__mockCalls = []; }")
            page.set_input_files("#fileInput", files=[{"name": "Contrato março.pdf", "mimeType": "application/pdf", "buffer": PDF}])
            page.wait_for_function("() => (document.getElementById('titleText')?.textContent||'').includes('Contrato')", timeout=30000)
            page.wait_for_function("() => !!globalThis.InkDOSBetaToolsProvider")
            page.click('[data-frame-action="sun"]')
            page.click(".inkdos-settings-option[data-settings-value='beta-pdf']")
            page.wait_for_function("() => window.__mockCalls.some(c => c[0] === 'inkdos_beta_open_with_file')")
            calls = [c for c in page.evaluate("() => window.__mockCalls") if c[0] in ("inkdos_beta_open", "inkdos_beta_open_with_file")]
            assert len(calls) == 1 and calls[0][0] == "inkdos_beta_open_with_file", calls
            sent = calls[0][1]
            assert sent["bytes"] > 0 and sent["pdf"] == "%PDF-", sent
            assert sent["headers"] == {"x-inkdos-tool": "pdf", "x-inkdos-file-name": "Contrato%20mar%C3%A7o.pdf"}, sent
            page.evaluate("(pdf) => { window.__resultPdf = pdf; window.__mockListeners['inkdos-beta-result']({ payload: 'Contrato%20mar%C3%A7o-assinado.pdf' }); }", PDF.decode("latin-1"))
            page.wait_for_function("() => (document.getElementById('titleText')?.textContent||'').includes('assinado')", timeout=30000)
            assert any(c[0] == "inkdos_beta_take_result" for c in page.evaluate("() => window.__mockCalls"))
            assert not errors, errors
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
    print(f"Desktop beta tools menu ({browser_name}): OK")


if __name__ == "__main__":
    main()
