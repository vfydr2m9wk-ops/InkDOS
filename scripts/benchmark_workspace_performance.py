#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from playwright.sync_api import Browser, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("INKDOS_PERF_PORT", "8844"))
BASE = f"http://127.0.0.1:{PORT}"
BROWSER_NAME = os.environ.get("BROWSER", "chromium").strip().lower()
ITERATIONS = max(1, int(os.environ.get("INKDOS_PERF_ITERATIONS", "3")))
OUT = Path(os.environ.get("INKDOS_PERF_OUT", f"artifacts/performance/{BROWSER_NAME}"))
TIMEOUT_MS = int(os.environ.get("INKDOS_PERF_TIMEOUT_MS", "30000"))

APPS = {
    "documents": {
        "path": "/apps/documents/index.html?suite=1",
        "startup": "() => !!globalThis.InkDOS2Documents?.DocumentsApp && !!document.getElementById('fileInput')",
    },
    "spreadsheets": {
        "path": "/apps/spreadsheets/index.html?suite=1",
        "startup": "() => !!globalThis.__inkdosSpreadsheetsS1?.openController && !!document.getElementById('fileInput')",
    },
    "presentations": {
        "path": "/apps/presentations/index.html?suite=1",
        "startup": "() => !!globalThis.InkDOS2Presentations?.PptxWriter && !!globalThis.__inkdosPresentations && !!document.getElementById('fileInput')",
    },
    "pdf": {
        "path": "/apps/pdf/index.html?suite=1",
        "startup": "() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug?.fileOpen && !!document.getElementById('fileInput')",
    },
    "epub": {
        "path": "/apps/epub/index.html?suite=1",
        "startup": "() => !!document.getElementById('fileInput') && !!document.getElementById('emptyState')",
    },
    "txt": {
        "path": "/apps/txt/index.html?suite=1",
        "startup": "() => document.body?.dataset?.runtimeReady === 'true' && !!document.getElementById('fileInput')",
    },
}

MONITOR_SCRIPT = r"""
(() => {
  const state = globalThis.__inkdosPerfProbe = {
    lagSamples: [],
    longTasks: [],
    reset() {
      this.lagSamples.length = 0;
      this.longTasks.length = 0;
      this.resetAt = performance.now();
    },
    snapshot() {
      const over50 = this.lagSamples.filter(x => x > 50);
      return {
        lagCountOver50: over50.length,
        maxLagMs: this.lagSamples.length ? Math.max(...this.lagSamples) : 0,
        longTaskCount: this.longTasks.length,
        maxLongTaskMs: this.longTasks.length ? Math.max(...this.longTasks) : 0,
      };
    }
  };
  try {
    const po = new PerformanceObserver(list => {
      for (const entry of list.getEntries()) state.longTasks.push(entry.duration || 0);
    });
    po.observe({type: 'longtask', buffered: true});
  } catch (_) {}
  let expected = performance.now() + 25;
  const tick = () => {
    const now = performance.now();
    const lag = Math.max(0, now - expected);
    if (lag > 1) state.lagSamples.push(lag);
    expected = now + 25;
    setTimeout(tick, 25);
  };
  setTimeout(tick, 25);
})();
"""


def wait_port() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local performance server did not start")


def new_context(browser: Browser):
    context = browser.new_context(
        viewport={"width": 1280, "height": 820},
        service_workers="block",
    )
    context.add_init_script(MONITOR_SCRIPT)
    return context


def new_launch_context(browser: Browser, case: dict, data: bytes):
    context = browser.new_context(
        viewport={"width": 1280, "height": 820},
        service_workers="block",
    )
    context.add_init_script(MONITOR_SCRIPT)
    encoded = base64.b64encode(data).decode("ascii")
    name = json.dumps(case["file"])
    mime = json.dumps(case["mime"])
    context.add_init_script(
        f"""(() => {{
          const raw = atob({json.dumps(encoded)});
          const bytes = new Uint8Array(raw.length);
          for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
          const queue = {{
            consumer: null,
            setConsumer(fn) {{
              this.consumer = fn;
              Promise.resolve().then(() => fn({{
                files: [{{
                  kind: 'file',
                  async getFile() {{ return new File([bytes], {name}, {{type: {mime}}}); }}
                }}]
              }}));
            }}
          }};
          Object.defineProperty(globalThis, 'launchQueue', {{
            value: queue,
            configurable: true
          }});
        }})();"""
    )
    return context


def probe_reset(page: Page) -> None:
    page.evaluate("() => globalThis.__inkdosPerfProbe?.reset()")


def probe_snapshot(page: Page) -> dict:
    return page.evaluate(
        "() => globalThis.__inkdosPerfProbe?.snapshot?.() || "
        "({lagCountOver50:0,maxLagMs:0,longTaskCount:0,maxLongTaskMs:0})"
    )


def to_b64_expr(body: str) -> str:
    return f"""async () => {{
      const bytes = await (async () => {{ {body} }})();
      let s = '';
      const chunk = 0x8000;
      for (let i = 0; i < bytes.length; i += chunk) {{
        s += String.fromCharCode(...bytes.subarray(i, i + chunk));
      }}
      return btoa(s);
    }}"""


def build_browser_fixtures(browser: Browser) -> dict[str, bytes]:
    fixtures: dict[str, bytes] = {}

    context = new_context(browser)
    page = context.new_page()
    page.goto(BASE + APPS["documents"]["path"], wait_until="load", timeout=TIMEOUT_MS)
    page.wait_for_function(APPS["documents"]["startup"], timeout=TIMEOUT_MS)
    docx_b64 = page.evaluate(
        to_b64_expr(
            """
            const NS = globalThis.InkDOS2Documents;
            const app = NS.DocumentsApp;
            await app.newDocument();
            const host = document.getElementById('pagesHost');
            const pc = host.querySelector('.page-content');
            pc.innerHTML = '<p>InkDOS synthetic performance document.</p><p>Local-first benchmark fixture.</p>';
            const saved = await NS.DocxWriter.save(host, 'perf.docx', null, null);
            return new Uint8Array(await saved.blob.arrayBuffer());
            """
        )
    )
    fixtures["documents-docx"] = base64.b64decode(docx_b64)
    context.close()

    context = new_context(browser)
    page = context.new_page()
    page.goto(BASE + APPS["spreadsheets"]["path"], wait_until="load", timeout=TIMEOUT_MS)
    page.wait_for_function(APPS["spreadsheets"]["startup"], timeout=TIMEOUT_MS)
    xlsx_b64 = page.evaluate(
        to_b64_expr(
            """
            const api = globalThis.__inkdosSpreadsheetsS1;
            await api.openController.newWorkbook();
            api.editor.editor.commitValue('InkDOS synthetic workbook', 0, 0);
            api.editor.editor.commitValue('42', 1, 0);
            const blob = await globalThis.LocalXLSX.saveCopy(api.session.book);
            return new Uint8Array(await blob.arrayBuffer());
            """
        )
    )
    fixtures["spreadsheets-xlsx"] = base64.b64decode(xlsx_b64)
    context.close()

    context = new_context(browser)
    page = context.new_page()
    page.goto(BASE + APPS["presentations"]["path"], wait_until="load", timeout=TIMEOUT_MS)
    page.wait_for_function(APPS["presentations"]["startup"], timeout=TIMEOUT_MS)
    for count in (1, 44):
        pptx_b64 = page.evaluate(
            """async (count) => {
              const NS = globalThis.InkDOS2Presentations;
              const M = NS.PresentationModel;
              const src = new NS.PresentationSession();
              src.resetNew();
              const setTitle = (slide, text) => {
                const o = slide.objects[0];
                o.text = text;
                o.paragraphs = M.normalizeParagraphs(null, text, o);
              };
              setTitle(src.slides[0], 'InkDOS synthetic slide 1');
              for (let i = 2; i <= count; i++) {
                src.addSlide();
                setTitle(src.currentSlide, 'InkDOS synthetic slide ' + i);
              }
              src.setCurrentByIndex(0);
              const bytes = await NS.PptxWriter.build(src);
              let s = '';
              const chunk = 0x8000;
              for (let i = 0; i < bytes.length; i += chunk) {
                s += String.fromCharCode(...bytes.subarray(i, i + chunk));
              }
              return btoa(s);
            }""",
            count,
        )
        fixtures[f"presentations-pptx-{count}"] = base64.b64decode(pptx_b64)
    context.close()

    context = new_context(browser)
    page = context.new_page()
    page.goto(BASE + APPS["pdf"]["path"], wait_until="load", timeout=TIMEOUT_MS)
    page.wait_for_function(APPS["pdf"]["startup"], timeout=TIMEOUT_MS)
    for count in (1, 20):
        pdf_b64 = page.evaluate(
            """async (count) => {
              const pdf = await PDFLib.PDFDocument.create();
              for (let i = 1; i <= count; i++) {
                const p = pdf.addPage([612, 792]);
                p.drawText('InkDOS synthetic PDF page ' + i, {x: 48, y: 730, size: 18});
              }
              const bytes = new Uint8Array(await pdf.save());
              let s = '';
              const chunk = 0x8000;
              for (let i = 0; i < bytes.length; i += chunk) {
                s += String.fromCharCode(...bytes.subarray(i, i + chunk));
              }
              return btoa(s);
            }""",
            count,
        )
        fixtures[f"pdf-{count}"] = base64.b64decode(pdf_b64)
    context.close()

    return fixtures


def minimal_epub_bytes() -> bytes:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "perf.epub"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            z.writestr(
                "META-INF/container.xml",
                """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
            )
            z.writestr(
                "OEBPS/content.opf",
                """<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="id">perf</dc:identifier><dc:title>InkDOS Performance</dc:title><dc:language>en</dc:language>
  </metadata>
  <manifest><item id="c1" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="c1"/></spine>
</package>""",
            )
            z.writestr(
                "OEBPS/chapter.xhtml",
                """<!doctype html><html xmlns="http://www.w3.org/1999/xhtml"><body>
<h1>InkDOS synthetic EPUB</h1><p>Performance fixture.</p>
</body></html>""",
            )
        return path.read_bytes()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction))))
    return ordered[idx]


def summarize(samples: list[dict]) -> dict:
    metrics = {}
    for key in ("elapsedMs", "maxLagMs", "maxLongTaskMs"):
        vals = [float(x.get(key, 0)) for x in samples]
        metrics[key] = {
            "median": round(statistics.median(vals), 2),
            "p95": round(percentile(vals, 0.95), 2),
            "min": round(min(vals), 2),
            "max": round(max(vals), 2),
        }
    metrics["lagCountOver50"] = sum(int(x.get("lagCountOver50", 0)) for x in samples)
    metrics["longTaskCount"] = sum(int(x.get("longTaskCount", 0)) for x in samples)
    return metrics


def startup_sample(browser: Browser, app: str) -> dict:
    context = new_context(browser)
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    start = time.perf_counter()
    page.goto(BASE + APPS[app]["path"], wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    page.wait_for_function(APPS[app]["startup"], timeout=TIMEOUT_MS)
    elapsed = (time.perf_counter() - start) * 1000
    snap = probe_snapshot(page)
    context.close()
    return {"elapsedMs": round(elapsed, 2), "errors": errors, **snap}


OPEN_CASES = [
    {
        "name": "documents-docx",
        "app": "documents",
        "file": "perf.docx",
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "ready": "() => globalThis.InkDOS2Documents?.DocumentsApp?.session?.kind === 'docx' && !!document.querySelector('.page-content')",
    },
    {
        "name": "spreadsheets-xlsx",
        "app": "spreadsheets",
        "file": "perf.xlsx",
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ready": "() => !!globalThis.__inkdosSpreadsheetsS1?.session?.book?.loaded && document.getElementById('startState')?.hidden === true",
    },
    {
        "name": "presentations-pptx-1",
        "app": "presentations",
        "file": "perf-1.pptx",
        "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "ready": "() => globalThis.__inkdosPresentations?.session?.sourceKind === 'pptx' && globalThis.__inkdosPresentations.session.slides.length === 1 && document.getElementById('startState')?.hidden === true",
    },
    {
        "name": "presentations-pptx-44",
        "app": "presentations",
        "file": "perf-44.pptx",
        "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "ready": "() => globalThis.__inkdosPresentations?.session?.sourceKind === 'pptx' && globalThis.__inkdosPresentations.session.slides.length === 44 && document.getElementById('startState')?.hidden === true",
    },
    {
        "name": "pdf-1",
        "app": "pdf",
        "file": "perf-1.pdf",
        "mime": "application/pdf",
        "ready": "() => globalThis.InkDOS2PdfP4?.PdfStabilityDebug?.layout?.pageCount === 1 && !!document.querySelector('canvas')",
    },
    {
        "name": "pdf-20",
        "app": "pdf",
        "file": "perf-20.pdf",
        "mime": "application/pdf",
        "ready": "() => globalThis.InkDOS2PdfP4?.PdfStabilityDebug?.layout?.pageCount === 20 && !!document.querySelector('canvas')",
    },
    {
        "name": "epub",
        "app": "epub",
        "file": "perf.epub",
        "mime": "application/epub+zip",
        "ready": "() => document.getElementById('emptyState')?.hidden === true",
    },
    {
        "name": "txt",
        "app": "txt",
        "file": "perf.txt",
        "mime": "text/plain",
        "ready": "() => document.getElementById('startState')?.hidden === true && document.getElementById('editor')?.value?.includes('InkDOS synthetic text')",
    },
]


def open_sample(browser: Browser, case: dict, data: bytes) -> dict:
    context = new_context(browser)
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    app = case["app"]
    page.goto(BASE + APPS[app]["path"], wait_until="load", timeout=TIMEOUT_MS)
    page.wait_for_function(APPS[app]["startup"], timeout=TIMEOUT_MS)
    probe_reset(page)
    start = time.perf_counter()
    page.locator("#fileInput").set_input_files(
        files=[{"name": case["file"], "mimeType": case["mime"], "buffer": data}]
    )
    page.wait_for_function(case["ready"], timeout=TIMEOUT_MS)
    elapsed = (time.perf_counter() - start) * 1000
    snap = probe_snapshot(page)
    context.close()
    return {"elapsedMs": round(elapsed, 2), "errors": errors, **snap}


def cold_open_sample(browser: Browser, case: dict, data: bytes) -> dict:
    context = new_launch_context(browser, case, data)
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    app = case["app"]
    start = time.perf_counter()
    page.goto(BASE + APPS[app]["path"], wait_until="domcontentloaded", timeout=TIMEOUT_MS)
    page.wait_for_function(case["ready"], timeout=TIMEOUT_MS)
    elapsed = (time.perf_counter() - start) * 1000
    snap = probe_snapshot(page)
    post_ready = {}
    if case["app"] == "pdf":
        probe_reset(page)
        page.wait_for_timeout(1200)
        post_ready = page.evaluate(
            """() => {
              const probe = globalThis.__inkdosPerfProbe;
              const lag = probe?.snapshot?.() || {lagCountOver50:0,maxLagMs:0,longTaskCount:0,maxLongTaskMs:0};
              const resetAt = Number(probe?.resetAt || 0);
              const resources = performance.getEntriesByType('resource')
                .filter(e => e.startTime >= resetAt)
                .map(e => ({
                  name: new URL(e.name, location.href).pathname,
                  initiatorType: e.initiatorType || '',
                  transferSize: Number(e.transferSize || 0),
                  decodedBodySize: Number(e.decodedBodySize || 0)
                }));
              return {
                lagCountOver50: lag.lagCountOver50,
                maxLagMs: lag.maxLagMs,
                longTaskCount: lag.longTaskCount,
                maxLongTaskMs: lag.maxLongTaskMs,
                resourceBytes: resources.reduce((n,e)=>n+(e.decodedBodySize||e.transferSize||0),0),
                resources
              };
            }"""
        )
    context.close()
    return {"elapsedMs": round(elapsed, 2), "errors": errors, **snap, "postReady": post_ready}


def main() -> None:
    if BROWSER_NAME not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={BROWSER_NAME}")

    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, BROWSER_NAME).launch(headless=True)
            fixtures = build_browser_fixtures(browser)
            fixtures["epub"] = minimal_epub_bytes()
            fixtures["txt"] = b"InkDOS synthetic text performance fixture.\n" * 100

            startup = {}
            for app in APPS:
                samples = [startup_sample(browser, app) for _ in range(ITERATIONS)]
                startup[app] = {"samples": samples, "summary": summarize(samples)}

            opens = {}
            for case in OPEN_CASES:
                samples = [open_sample(browser, case, fixtures[case["name"]]) for _ in range(ITERATIONS)]
                opens[case["name"]] = {
                    "app": case["app"],
                    "bytes": len(fixtures[case["name"]]),
                    "samples": samples,
                    "summary": summarize(samples),
                }

            cold_opens = {}
            for case in OPEN_CASES:
                samples = [cold_open_sample(browser, case, fixtures[case["name"]]) for _ in range(ITERATIONS)]
                cold_opens[case["name"]] = {
                    "app": case["app"],
                    "bytes": len(fixtures[case["name"]]),
                    "samples": samples,
                    "summary": summarize(samples),
                }

            browser.close()

        report = {
            "browser": BROWSER_NAME,
            "iterations": ITERATIONS,
            "serviceWorkers": "blocked to isolate workspace runtime; snapshot update measured separately",
            "environment": "headless Playwright synthetic benchmark; not a XeOS/iPad device timing claim",
            "startup": startup,
            "open": opens,
            "coldOpen": cold_opens,
        }
        (OUT / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(
            {
                "browser": BROWSER_NAME,
                "startupMedianMs": {k: v["summary"]["elapsedMs"]["median"] for k, v in startup.items()},
                "openMedianMs": {k: v["summary"]["elapsedMs"]["median"] for k, v in opens.items()},
                "coldOpenMedianMs": {k: v["summary"]["elapsedMs"]["median"] for k, v in cold_opens.items()},
            },
            indent=2,
        ))
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
