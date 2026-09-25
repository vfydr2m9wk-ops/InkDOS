#!/usr/bin/env python3
"""Component-isolated performance benchmark for the autonomous InkDOS lab.

Runs exactly one workspace so a broken startup/fixture in a sibling app cannot
erase otherwise valid quick evidence. Full cross-app/cross-browser validation
remains the responsibility of PR #203.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys

from playwright.sync_api import Page, sync_playwright

import benchmark_workspace_performance as perf

COMPONENT = os.environ.get("INKDOS_PERF_COMPONENT", "").strip().lower()
SUPPORTED = {"documents", "spreadsheets", "presentations", "pdf", "epub", "txt"}


def _wait_startup(page: Page, component: str, phase: str) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    try:
        page.wait_for_function(perf.APPS[component]["startup"], timeout=perf.TIMEOUT_MS)
    except Exception as exc:
        diag = perf.OUT / "diagnostics"
        diag.mkdir(parents=True, exist_ok=True)
        try:
            page.screenshot(path=str(diag / f"{component}-{phase}-timeout.png"), full_page=False)
        except Exception:
            pass
        (diag / f"{component}-{phase}-failure.json").write_text(
            json.dumps(
                {
                    "component": component,
                    "phase": phase,
                    "error": str(exc),
                    "pageErrors": errors,
                    "url": page.url,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        raise RuntimeError(
            f"{component} {phase} startup failed; diagnostics written to {diag}"
        ) from exc


def _documents_fixture(browser) -> dict[str, bytes]:
    context = perf.new_context(browser)
    page = context.new_page()
    page.goto(perf.BASE + perf.APPS["documents"]["path"], wait_until="load", timeout=perf.TIMEOUT_MS)
    _wait_startup(page, "documents", "fixture")
    data = page.evaluate(
        perf.to_b64_expr(
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
    context.close()
    return {"documents-docx": base64.b64decode(data)}


def _spreadsheets_fixture(browser) -> dict[str, bytes]:
    context = perf.new_context(browser)
    page = context.new_page()
    page.goto(perf.BASE + perf.APPS["spreadsheets"]["path"], wait_until="load", timeout=perf.TIMEOUT_MS)
    _wait_startup(page, "spreadsheets", "fixture")
    data = page.evaluate(
        perf.to_b64_expr(
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
    context.close()
    return {"spreadsheets-xlsx": base64.b64decode(data)}


def _presentations_fixture(browser) -> dict[str, bytes]:
    fixtures: dict[str, bytes] = {}
    context = perf.new_context(browser)
    page = context.new_page()
    page.goto(perf.BASE + perf.APPS["presentations"]["path"], wait_until="load", timeout=perf.TIMEOUT_MS)
    _wait_startup(page, "presentations", "fixture")
    for count in (1, 44):
        data = page.evaluate(
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
        fixtures[f"presentations-pptx-{count}"] = base64.b64decode(data)
    context.close()
    return fixtures


def _pdf_fixture(browser) -> dict[str, bytes]:
    fixtures: dict[str, bytes] = {}
    context = perf.new_context(browser)
    page = context.new_page()
    page.goto(perf.BASE + perf.APPS["pdf"]["path"], wait_until="load", timeout=perf.TIMEOUT_MS)
    _wait_startup(page, "pdf", "fixture")
    page.add_script_tag(url=perf.BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
    page.wait_for_function("() => !!globalThis.PDFLib?.PDFDocument", timeout=perf.TIMEOUT_MS)
    for count in (1, 20):
        data = page.evaluate(
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
        fixtures[f"pdf-{count}"] = base64.b64decode(data)
    context.close()
    return fixtures


def _fixtures(browser) -> dict[str, bytes]:
    if COMPONENT == "documents":
        return _documents_fixture(browser)
    if COMPONENT == "spreadsheets":
        return _spreadsheets_fixture(browser)
    if COMPONENT == "presentations":
        return _presentations_fixture(browser)
    if COMPONENT == "pdf":
        return _pdf_fixture(browser)
    if COMPONENT == "epub":
        return {"epub": perf.minimal_epub_bytes()}
    if COMPONENT == "txt":
        return {"txt": b"InkDOS synthetic text performance fixture.\n" * 100}
    raise AssertionError(COMPONENT)


def _visual(browser, fixtures: dict[str, bytes], cases: list[dict]) -> dict:
    if not perf.VISUAL_ENABLED:
        return {"enabled": False, "reason": "INKDOS_PERF_VISUAL disabled"}

    visual_dir = perf.OUT / "visual"
    result = {
        "component": COMPONENT,
        "note": "Component-isolated quick evidence; full cross-app visual audit remains PR #203.",
        "themes": list(perf.VISUAL_THEMES),
        "timelineTargetsMs": list(perf.VISUAL_TARGETS_MS),
        "startup": {},
        "coldOpen": {},
    }
    for appearance in perf.VISUAL_THEMES:
        result["startup"][appearance] = {
            COMPONENT: perf.visual_startup_capture(browser, COMPONENT, appearance, visual_dir)
        }
        result["coldOpen"][appearance] = {}
        for case in cases:
            result["coldOpen"][appearance][case["name"]] = perf.visual_cold_open_capture(
                browser, case, fixtures[case["name"]], appearance, visual_dir
            )

    (perf.OUT / "visual-report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    if COMPONENT not in SUPPORTED:
        raise SystemExit("INKDOS_PERF_COMPONENT must be one of: " + ", ".join(sorted(SUPPORTED)))
    if perf.BROWSER_NAME not in {"chromium", "firefox", "webkit"}:
        raise RuntimeError(f"Unsupported BROWSER={perf.BROWSER_NAME}")

    perf.OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(perf.PORT), "--bind", "127.0.0.1"],
        cwd=perf.ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        perf.wait_port()
        with sync_playwright() as pw:
            browser = getattr(pw, perf.BROWSER_NAME).launch(headless=True)
            fixtures = _fixtures(browser)
            cases = [case for case in perf.OPEN_CASES if case["app"] == COMPONENT]

            startup_samples = [
                perf.startup_sample(browser, COMPONENT) for _ in range(perf.ITERATIONS)
            ]
            startup = {
                COMPONENT: {
                    "samples": startup_samples,
                    "summary": perf.summarize(startup_samples),
                }
            }

            opens = {}
            cold_opens = {}
            for case in cases:
                data = fixtures[case["name"]]
                samples = [
                    perf.open_sample(browser, case, data) for _ in range(perf.ITERATIONS)
                ]
                opens[case["name"]] = {
                    "app": COMPONENT,
                    "bytes": len(data),
                    "samples": samples,
                    "summary": perf.summarize(samples),
                }
                cold_samples = [
                    perf.cold_open_sample(browser, case, data)
                    for _ in range(perf.ITERATIONS)
                ]
                cold_opens[case["name"]] = {
                    "app": COMPONENT,
                    "bytes": len(data),
                    "samples": cold_samples,
                    "summary": perf.summarize(cold_samples),
                }

            visual = _visual(browser, fixtures, cases)
            browser.close()

        report = {
            "browser": perf.BROWSER_NAME,
            "component": COMPONENT,
            "iterations": perf.ITERATIONS,
            "serviceWorkers": "blocked to isolate workspace runtime; full snapshot audit remains PR #203",
            "environment": "headless Playwright component-isolated quick benchmark; not a XeOS/iPad timing claim",
            "startup": startup,
            "open": opens,
            "coldOpen": cold_opens,
            "visual": visual,
        }
        (perf.OUT / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "browser": perf.BROWSER_NAME,
                    "component": COMPONENT,
                    "startupMedianMs": startup[COMPONENT]["summary"]["elapsedMs"]["median"],
                    "openMedianMs": {k: v["summary"]["elapsedMs"]["median"] for k, v in opens.items()},
                    "coldOpenMedianMs": {k: v["summary"]["elapsedMs"]["median"] for k, v in cold_opens.items()},
                },
                indent=2,
            )
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
