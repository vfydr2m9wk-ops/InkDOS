#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "tests" / "browser" / "results" / "visual_foundation_0203.json"


def read_css(*relatives: str) -> str:
    return "\n".join((ROOT / relative).read_text(encoding="utf-8") for relative in relatives)


OVERLAY = read_css("shared/ui/visual-foundation-v0203.css")
HOME_CSS = read_css("shared/hub.css") + "\n" + OVERLAY
WORKSPACE_SHARED_CSS = read_css(
    "shared/office-shell.css",
    "shared/ui/design-tokens.css",
    "shared/ui/components.css",
    "shared/ui/workspace-layout.css",
    "shared/ui/visual-foundation.css",
) + "\n" + OVERLAY
DOCUMENTS_CSS = read_css("apps/documents/styles.css") + "\n" + WORKSPACE_SHARED_CSS
EPUB_CSS = read_css("apps/epub/styles.css") + "\n" + WORKSPACE_SHARED_CSS


def main() -> int:
    browser_name = os.environ.get("INKDESK_BROWSER", "chromium").strip().lower()
    with sync_playwright() as p:
        launcher = getattr(p, browser_name)
        launch_kwargs = {}
        executable = (os.environ.get("CHROMIUM_PATH") or os.environ.get("INKDESK_BROWSER_EXECUTABLE", "")).strip()
        if executable and browser_name == "chromium":
            launch_kwargs["executable_path"] = executable
            launch_kwargs["args"] = ["--no-sandbox"]
        browser = launcher.launch(headless=True, **launch_kwargs)
        page = browser.new_page(viewport={"width": 1180, "height": 800})
        home_html = """<!doctype html><style>{}</style><body>
        <main class="hub-shell">
          <header class="hub-topbar">
            <a class="brand-lockup"><span class="brand-mark"></span><span class="brand-copy"><strong>InkDesk</strong><small>Local-first workspace</small></span></a>
            <span class="release-badge">v0.20.3.0 beta</span>
          </header>
          <section class="hub-intro"><h1>Choose a workspace</h1></section>
          <section class="workspace-grid">
            <a class="workspace-card documents"><span class="app-icon">D</span><span class="workspace-copy"><strong>Documents</strong><small>DOCX</small></span><span class="open-arrow">›</span></a>
            <a class="workspace-card spreadsheets"><span class="app-icon">S</span><span class="workspace-copy"><strong>Spreadsheets</strong><small>XLSX</small></span><span class="open-arrow">›</span></a>
            <a class="workspace-card epub"><span class="app-icon">E</span><span class="workspace-copy"><strong>EPUB</strong><small>EPUB</small></span><span class="open-arrow">›</span></a>
          </section>
        </main></body>""".format(HOME_CSS)
        page.set_content(home_html)
        desktop_cols = page.locator('.workspace-grid').evaluate("el => getComputedStyle(el).gridTemplateColumns.split(' ').length")
        card_radius = page.locator('.workspace-card').first.evaluate("el => getComputedStyle(el).borderRadius")
        document_icon = page.locator('.workspace-card.documents .app-icon').evaluate("el => getComputedStyle(el).backgroundImage")
        page.set_viewport_size({"width": 390, "height": 780})
        phone_cols = page.locator('.workspace-grid').evaluate("el => getComputedStyle(el).gridTemplateColumns.split(' ').length")

        page.set_content("<!doctype html><style>{}</style><body class='office-product office-documents'><header class='topbar'><button class='icon-btn'>A</button></header></body>".format(DOCUMENTS_CSS))
        title_height = page.locator('.topbar').evaluate("el => getComputedStyle(el).minHeight")
        doc_accent = page.locator('body').evaluate("el => getComputedStyle(el).getPropertyValue('--ink-accent').trim()")
        page.set_content("<!doctype html><style>{}</style><body class='office-product office-epub'><header class='epub-titlebar'></header></body>".format(EPUB_CSS))
        epub_accent = page.locator('body').evaluate("el => getComputedStyle(el).getPropertyValue('--ink-accent').trim()")
        browser.close()

    result = {
        "desktop_columns": desktop_cols,
        "phone_columns": phone_cols,
        "card_radius": card_radius,
        "documents_icon_preserved": "documents.svg" in document_icon,
        "titlebar_min_height": title_height,
        "documents_accent": doc_accent,
        "epub_accent": epub_accent,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert desktop_cols == 3, result
    assert phone_cols == 1, result
    assert "documents.svg" in document_icon, result
    assert title_height == "44px", result
    assert doc_accent == "#2f6fed", result
    assert epub_accent == "#7655c7", result
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
