#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = 8812
BASE = f"http://127.0.0.1:{PORT}"
CYCLES = max(2, int(os.environ.get("INKDOS_STATEFUL_CYCLES", "3")))
REPORT = ROOT / "artifacts" / "behavioral-stability" / "stateful-soak.json"

WORKSPACES = (
    ("documents", "/apps/documents/", "() => !!globalThis.InkDOS2Documents?.DocumentsDebug?.executeCommand"),
    ("spreadsheets", "/apps/spreadsheets/", "() => !!globalThis.__inkdosSpreadsheetsS1"),
    ("presentations", "/apps/presentations/", "() => !!globalThis.__inkdosPresentations?.p1Tools"),
    ("txt", "/apps/txt/", "() => document.body.dataset.runtimeReady === 'true' && !!globalThis.InkDOS2?.TxtAppDebug"),
    ("epub", "/apps/epub/", "() => !!globalThis.__InkEpubR4"),
    ("pdf", "/apps/pdf/", "() => !!globalThis.InkDOS2PdfP4?.PdfStabilityDebug"),
)

NEW_PROBES = {
    "documents": (
        "#startNew",
        "() => document.getElementById('startState').hidden && document.querySelectorAll('#pagesHost .doc-page').length >= 1",
    ),
    "spreadsheets": (
        "#startNew",
        "() => document.getElementById('startState').hidden && !!globalThis.__inkdosSpreadsheetsS1?.session?.book?.loaded",
    ),
    "presentations": (
        "#startNew",
        "() => document.getElementById('startState').hidden && globalThis.__inkdosPresentations?.session?.active && globalThis.__inkdosPresentations.session.slides.length === 1",
    ),
    "txt": (
        "#startNew",
        "() => document.getElementById('startState').hidden && !!globalThis.InkDOS2?.TxtAppDebug?.state?.loaded",
    ),
}


def wait_port(timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError("Local stateful soak server did not start")


def stop_server(server: subprocess.Popen | None) -> None:
    if server is None or server.poll() is not None:
        return
    server.terminate()
    try:
        server.wait(timeout=3)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=3)


def dom_probe(page):
    return page.evaluate(
        """() => {
            const ids = new Map();
            for (const el of document.querySelectorAll('[id]')) {
                ids.set(el.id, (ids.get(el.id) || 0) + 1);
            }
            const duplicateIds = [...ids.entries()].filter(([, count]) => count > 1);
            const body = document.body;
            return {
                title: document.title,
                readyState: document.readyState,
                elements: document.querySelectorAll('*').length,
                buttons: document.querySelectorAll('button').length,
                dialogs: document.querySelectorAll('dialog,[role="dialog"]').length,
                duplicateIds,
                bodyWidth: body ? body.getBoundingClientRect().width : 0,
                bodyHeight: body ? body.getBoundingClientRect().height : 0,
                scrollWidth: document.documentElement.scrollWidth,
                scrollHeight: document.documentElement.scrollHeight,
            };
        }"""
    )


def semantic_probe(page, name: str):
    if name == "documents":
        return page.evaluate(
            """() => ({
                pages: document.querySelectorAll('#pagesHost .doc-page').length,
                active: !document.getElementById('startState').hidden,
                undoDisabled: document.getElementById('undoBtn')?.disabled ?? null,
                redoDisabled: document.getElementById('redoBtn')?.disabled ?? null,
            })"""
        )
    if name == "spreadsheets":
        return page.evaluate(
            """() => {
                const s = globalThis.__inkdosSpreadsheetsS1?.session;
                return {
                    loaded: !!s?.book?.loaded,
                    sheets: s?.book?.sheets?.length || 0,
                    dirty: !!s?.dirty,
                    fileName: s?.fileName || '',
                };
            }"""
        )
    if name == "presentations":
        return page.evaluate(
            """() => {
                const s = globalThis.__inkdosPresentations?.session;
                return {
                    active: !!s?.active,
                    slides: s?.slides?.length || 0,
                    currentIndex: s?.currentIndex ?? null,
                    dirty: !!s?.dirty,
                };
            }"""
        )
    if name == "txt":
        return page.evaluate(
            """() => {
                const d = globalThis.InkDOS2?.TxtAppDebug;
                return {
                    loaded: !!d?.state?.loaded,
                    dirty: !!d?.state?.session?.dirty,
                    length: document.getElementById('editor')?.value?.length ?? 0,
                    wrap: d?.state?.wrap ?? null,
                };
            }"""
        )
    return {}


def main() -> None:
    browser_name = os.environ.get("BROWSER", "chromium").strip().lower()
    if browser_name not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={browser_name}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    server: subprocess.Popen | None = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    report = {
        "browser": browser_name,
        "cycles": CYCLES,
        "workspaces": {name: [] for name, _, _ in WORKSPACES},
        "errors": [],
        "replay": f"BROWSER={browser_name} INKDOS_STATEFUL_CYCLES={CYCLES} python tests/test_cross_suite_stateful_soak_browser.py",
    }
    phase = "bootstrap"
    errors: list[str] = []

    try:
        wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, browser_name).launch(headless=True)
            context = browser.new_context(viewport={"width": 1360, "height": 900})
            page = context.new_page()
            page.on("pageerror", lambda exc: errors.append(f"{phase} pageerror: {exc}"))
            page.on(
                "console",
                lambda msg: errors.append(f"{phase} console.error: {msg.text}") if msg.type == "error" else None,
            )
            cdp = context.new_cdp_session(page) if browser_name == "chromium" else None

            page.goto(BASE + "/index.html", wait_until="load")
            assert page.evaluate("() => 'serviceWorker' in navigator") is True
            page.evaluate("async () => { await navigator.serviceWorker.ready; return true; }")
            page.reload(wait_until="load")
            page.wait_for_function("() => !!navigator.serviceWorker.controller", timeout=15_000)

            for cycle in range(1, CYCLES + 1):
                for name, path, ready in WORKSPACES:
                    phase = f"cycle:{cycle}:{name}"
                    errors.clear()
                    page.goto(BASE + path, wait_until="load", timeout=20_000)
                    page.wait_for_function(ready, timeout=15_000)

                    before = dom_probe(page)
                    assert before["title"].strip(), (phase, before)
                    assert before["readyState"] == "complete", (phase, before)
                    assert before["bodyWidth"] > 0 and before["bodyHeight"] > 0, (phase, before)
                    assert before["duplicateIds"] == [], (phase, before["duplicateIds"])

                    if name in NEW_PROBES:
                        selector, active_ready = NEW_PROBES[name]
                        locator = page.locator(selector)
                        assert locator.count() == 1, (phase, selector, locator.count())
                        if locator.is_visible():
                            locator.click()
                            page.wait_for_function(active_ready, timeout=10_000)

                    after = dom_probe(page)
                    assert after["duplicateIds"] == [], (phase, after["duplicateIds"])
                    semantic = semantic_probe(page, name)

                    metrics = {}
                    if cdp is not None:
                        try:
                            cdp.send("HeapProfiler.collectGarbage")
                            heap = cdp.send("Runtime.getHeapUsage")
                            dom = cdp.send("Memory.getDOMCounters")
                            metrics = {
                                "usedHeap": int(heap.get("usedSize", 0)),
                                "totalHeap": int(heap.get("totalSize", 0)),
                                "documents": int(dom.get("documents", 0)),
                                "nodes": int(dom.get("nodes", 0)),
                                "jsEventListeners": int(dom.get("jsEventListeners", 0)),
                            }
                        except Exception as exc:
                            metrics = {"metricsError": str(exc)}

                    if errors:
                        raise AssertionError({"phase": phase, "errors": list(errors)})

                    report["workspaces"][name].append(
                        {
                            "cycle": cycle,
                            "domBefore": before,
                            "domAfter": after,
                            "semantic": semantic,
                            "metrics": metrics,
                        }
                    )

            # Heuristic leak guard. These limits are intentionally broad: the gate
            # catches runaway retention/duplication, while the raw metrics remain in
            # the artifact for trend comparison between releases.
            if browser_name == "chromium":
                for name, samples in report["workspaces"].items():
                    metric_samples = [x["metrics"] for x in samples if x["metrics"].get("usedHeap")]
                    if len(metric_samples) < 2:
                        continue
                    first = metric_samples[0]
                    last = metric_samples[-1]
                    assert last["usedHeap"] <= first["usedHeap"] * 4 + 128 * 1024 * 1024, (
                        name,
                        "catastrophic heap growth",
                        first,
                        last,
                    )
                    assert last["nodes"] <= first["nodes"] * 4 + 10_000, (
                        name,
                        "catastrophic DOM node retention",
                        first,
                        last,
                    )
                    assert last["jsEventListeners"] <= first["jsEventListeners"] * 4 + 2_000, (
                        name,
                        "catastrophic event-listener retention",
                        first,
                        last,
                    )

            context.close()
            browser.close()

        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Cross-suite stateful soak ({browser_name}, {CYCLES} cycles): OK")
        print(f"Report: {REPORT.relative_to(ROOT)}")
    except Exception as exc:
        report["errors"].append({"phase": phase, "error": repr(exc), "events": list(errors)})
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"REPLAY: {report['replay']}", file=sys.stderr)
        raise
    finally:
        stop_server(server)


if __name__ == "__main__":
    main()
