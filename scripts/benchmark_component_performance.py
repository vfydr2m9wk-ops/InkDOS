#!/usr/bin/env python3
"""Component-isolated WebKit performance benchmark for the autonomous lab.

Unlike benchmark_workspace_performance.py, this runner creates fixtures and
collects evidence for exactly one component so a broken fixture/startup in a
sibling app cannot erase otherwise valid quick evidence.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

import benchmark_workspace_performance as perf

COMPONENT = os.environ.get("INKDOS_PERF_COMPONENT", "").strip().lower()
SUPPORTED = {"presentations", "pdf"}


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
        payload = {
            "component": component,
            "phase": phase,
            "error": str(exc),
            "pageErrors": errors,
            "url": page.url,
        }
        (diag / f"{component}-{phase}-failure.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        raise RuntimeError(
            f"{component} {phase} startup failed; diagnostics written to {diag}"
        ) from exc


def _build_presentations_fixtures(browser) -> dict[str, bytes]:
    fixtures: dict[str, bytes] = {}
    context = perf.new_context(browser)
    page = context.new_page()
    page.goto(
        perf.BASE + perf.APPS["presentations"]["path"],
        wait_until="load",
        timeout=perf.TIMEOUT_MS,
    )
    _wait_startup(page, "presentations", "fixture")
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
    return fixtures


def _build_pdf_fixtures(browser) -> dict[str, bytes]:
    fixtures: dict[str, bytes] = {}
    context = perf.new_context(browser)
    page = context.new_page()
    page.goto(
        perf.BASE + perf.APPS["pdf"]["path"],
        wait_until="load",
        timeout=perf.TIMEOUT_MS,
    )
    _wait_startup(page, "pdf", "fixture")
    page.add_script_tag(url=perf.BASE + "/apps/pdf/vendor/pdf-lib/pdf-lib.min.js")
    page.wait_for_function(
        "() => !!globalThis.PDFLib?.PDFDocument",
        timeout=perf.TIMEOUT_MS,
    )
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
            COMPONENT: perf.visual_startup_capture(
                browser, COMPONENT, appearance, visual_dir
            )
        }
        result["coldOpen"][appearance] = {}
        for case in cases:
            result["coldOpen"][appearance][case["name"]] = perf.visual_cold_open_capture(
                browser,
                case,
                fixtures[case["name"]],
                appearance,
                visual_dir,
            )
    (perf.OUT / "visual-report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    if COMPONENT not in SUPPORTED:
        raise SystemExit(
            "INKDOS_PERF_COMPONENT must be one of: " + ", ".join(sorted(SUPPORTED))
        )
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
            fixtures = (
                _build_presentations_fixtures(browser)
                if COMPONENT == "presentations"
                else _build_pdf_fixtures(browser)
            )
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
                    perf.open_sample(browser, case, data)
                    for _ in range(perf.ITERATIONS)
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
            "environment": "headless Playwright component-isolated quick benchmark; not a XeOS/iPad device timing claim",
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
                    "openMedianMs": {
                        k: v["summary"]["elapsedMs"]["median"] for k, v in opens.items()
                    },
                    "coldOpenMedianMs": {
                        k: v["summary"]["elapsedMs"]["median"] for k, v in cold_opens.items()
                    },
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
