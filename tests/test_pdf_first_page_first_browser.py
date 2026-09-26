#!/usr/bin/env python3
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
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    errors: list[str] = []
    try:
        wait_port(PORT)
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
            page.on(
                "console",
                lambda msg: errors.append(f"console.error: {msg.text}")
                if msg.type == "error"
                else None,
            )
            page.goto(BASE + "/apps/pdf/", wait_until="load")
            page.wait_for_function("() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug")
            page.add_script_tag(url=BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
            page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument", timeout=15000)

            probe = page.evaluate(r"""async () => {
              const d = globalThis.InkDOS2PdfP4.PdfStabilityDebug;
              const pdf = await PDFLib.PDFDocument.create();
              const p1 = pdf.addPage([612, 792]);
              p1.drawText('First page must render before bulk work', {x:48, y:730, size:20});
              const p2 = pdf.addPage([612, 792]);
              p2.drawText('Second page background work', {x:48, y:730, size:20});
              const attachment = new Uint8Array(512 * 1024);
              let entropy = 0x9e3779b9;
              for (let i = 0; i < attachment.length; i++) {
                entropy ^= entropy << 13;
                entropy ^= entropy >>> 17;
                entropy ^= entropy << 5;
                attachment[i] = entropy & 0xff;
              }
              await pdf.attach(attachment, 'deferred-payload.bin', {mimeType:'application/octet-stream'});
              const bytes = new Uint8Array(await pdf.save({useObjectStreams:false}));
              if (bytes.length <= 65536) throw new Error('Fixture is too small for range-read validation');

              const file = new File([bytes], 'first-page-first.pdf', {type:'application/pdf'});
              const nativeArrayBuffer = file.arrayBuffer.bind(file);
              const nativeSlice = file.slice.bind(file);
              globalThis.__pdfWholeReads = 0;
              globalThis.__pdfRangeIntervals = [];
              Object.defineProperty(file, 'arrayBuffer', {
                configurable: true,
                value: async () => {
                  globalThis.__pdfWholeReads += 1;
                  return nativeArrayBuffer();
                }
              });
              Object.defineProperty(file, 'slice', {
                configurable: true,
                value: (start, end, type) => {
                  const a = Math.max(0, Number(start) || 0);
                  const b = end == null ? file.size : Math.max(a, Math.min(file.size, Number(end) || 0));
                  globalThis.__pdfRangeIntervals.push([a, b]);
                  return nativeSlice(start, end, type);
                }
              });

              const events = [];
              const originalAround = d.layout.ensureAround.bind(d.layout);
              const originalRendered = d.layout.onPageRendered;
              d.layout.ensureAround = async (...args) => {
                events.push({name:'background', at:performance.now()});
                return originalAround(...args);
              };
              d.layout.onPageRendered = async info => {
                if (info.pageNumber === 1 && !events.some(e => e.name === 'page1')) {
                  events.push({name:'page1', at:performance.now()});
                }
                return await originalRendered(info);
              };

              const t0 = performance.now();
              const opening = d.fileOpen.openFile(file);
               await new Promise(resolve => requestAnimationFrame(resolve));
               const loadingVisibleDuringOpen = !document.getElementById('pdfLoading').hidden;
               const opened = await opening;
              const deadline = performance.now() + 15000;
              while (!document.querySelector('.pdf-page-canvas')) {
                if (performance.now() > deadline) throw new Error('First page did not render');
                await new Promise(resolve => requestAnimationFrame(resolve));
              }

              function covered(intervals) {
                const sorted = intervals.slice().sort((a,b) => a[0]-b[0] || a[1]-b[1]);
                let total = 0, start = -1, end = -1;
                for (const pair of sorted) {
                  if (start < 0) { start = pair[0]; end = pair[1]; continue; }
                  if (pair[0] <= end) end = Math.max(end, pair[1]);
                  else { total += end - start; start = pair[0]; end = pair[1]; }
                }
                if (start >= 0) total += end - start;
                return total;
              }

              const page1 = events.find(e => e.name === 'page1');
              return {
                opened,
                size: bytes.length,
                wholeReads: globalThis.__pdfWholeReads,
                rangedBytesAtFirstPaint: covered(globalThis.__pdfRangeIntervals),
                sourcePending: d.session.sourcePending,
                sourceLength: d.session.sourceBytes.length,
                events: events.map(e => e.name),
                firstPaintMs: page1 ? page1.at - t0 : null,
                 loadingVisibleDuringOpen,
                 loadingHiddenAfterPaint: document.getElementById('pdfLoading').hidden,
              };
            }""")

            assert probe["opened"] is True, probe
            assert probe["size"] > 65536, probe
            assert probe["wholeReads"] == 0, probe
            assert probe["sourcePending"] is True, probe
            assert probe["sourceLength"] == 0, probe
            assert probe["rangedBytesAtFirstPaint"] < probe["size"], probe
            assert "page1" in probe["events"], probe
            assert probe["loadingVisibleDuringOpen"] is True, probe
            assert probe["loadingHiddenAfterPaint"] is True, probe
            if "background" in probe["events"]:
                assert probe["events"].index("page1") < probe["events"].index("background"), probe

            materialized = page.evaluate(r"""async () => {
              const d = globalThis.InkDOS2PdfP4.PdfStabilityDebug;
              const bytes = await d.session.ensureSourceBytes();
              return {
                wholeReads: globalThis.__pdfWholeReads,
                sourcePending: d.session.sourcePending,
                sourceLength: bytes.length,
              };
            }""")
            assert materialized["wholeReads"] == 1, materialized
            assert materialized["sourcePending"] is False, materialized
            assert materialized["sourceLength"] == probe["size"], (probe, materialized)

            browser.close()

        if errors:
            raise AssertionError({"browser": browser_name, "errors": errors})
        print(
            f"PDF first-page-first regression passed on {browser_name}: "
            f"firstPaintMs={probe['firstPaintMs']:.1f}, "
            f"ranged={probe['rangedBytesAtFirstPaint']}/{probe['size']} bytes"
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
