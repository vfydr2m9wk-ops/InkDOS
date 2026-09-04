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


OVERLAY = read_css("shared/ui/visual.css", "shared/ui/workspace.css")
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
SPREADSHEETS_CSS = read_css("apps/spreadsheets/styles.css") + "\n" + WORKSPACE_SHARED_CSS
PRESENTATIONS_CSS = read_css("apps/presentations/styles.css") + "\n" + WORKSPACE_SHARED_CSS
PDF_CSS = read_css("apps/pdf/styles.css") + "\n" + WORKSPACE_SHARED_CSS


def main() -> int:
    browser_name = os.environ.get("INKDOS_BROWSER", "chromium").strip().lower()
    with sync_playwright() as p:
        launcher = getattr(p, browser_name)
        launch_kwargs = {}
        executable = (os.environ.get("CHROMIUM_PATH") or os.environ.get("INKDOS_BROWSER_EXECUTABLE", "")).strip()
        if executable and browser_name == "chromium":
            launch_kwargs["executable_path"] = executable
            launch_kwargs["args"] = ["--no-sandbox"]
        browser = launcher.launch(headless=True, **launch_kwargs)
        page = browser.new_page(viewport={"width": 1180, "height": 800})
        home_html = """<!doctype html><style>{}</style><body>
        <main class="hub-shell">
          <header class="hub-topbar">
            <a class="brand-lockup"><span class="brand-mark"></span><span class="brand-copy"><strong>InkDOS</strong><small>Local-first workspace</small></span></a>
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

        # Reset to the desktop/tablet validation viewport after the launcher phone check.
        page.set_viewport_size({"width": 1180, "height": 800})

        page.set_content("<!doctype html><style>{}</style><body class='office-product office-documents'><header class='topbar'><button class='icon-btn'>A</button></header></body>".format(DOCUMENTS_CSS))
        title_height = page.locator('.topbar').evaluate("el => getComputedStyle(el).minHeight")
        doc_accent = page.locator('body').evaluate("el => getComputedStyle(el).getPropertyValue('--ink-accent').trim()")
        page.set_content("<!doctype html><style>{}</style><body class='office-product office-epub'><header class='epub-titlebar'></header></body>".format(EPUB_CSS))
        epub_accent = page.locator('body').evaluate("el => getComputedStyle(el).getPropertyValue('--ink-accent').trim()")

        page.set_content("""<!doctype html><style>{}</style><body class='office-product office-spreadsheets'>
          <header class='titlebar'><div class='left'></div><div class='document-title'><input class='title-input'></div><div class='right'><button id='saveBtn'></button></div></header>
          <footer><div></div><div class='status'></div></footer>
        </body>""".format(SPREADSHEETS_CSS))
        sheets_title_display = page.locator('.titlebar').evaluate("el => getComputedStyle(el).display")
        sheets_title_position = page.locator('.document-title').evaluate("el => getComputedStyle(el).position")
        sheets_footer_height = page.locator('footer').evaluate("el => getComputedStyle(el).height")

        page.set_content("""<!doctype html><style>{}</style><body class='office-product office-presentations'>
          <main class='app hide-notes'><header class='titlebar'></header><nav class='toolbar'></nav><div class='tools'></div>
          <section class='workspace hide-inspector'><aside class='slide-list'></aside><section class='stage-wrap'></section><aside class='inspector'></aside></section>
          <section class='notes-panel'></section><footer class='statusbar'></footer></main>
        </body>""".format(PRESENTATIONS_CSS))
        presentation_panel_shadow = page.locator('.slide-list').evaluate("el => getComputedStyle(el).boxShadow")
        presentation_panel_radius = page.locator('.slide-list').evaluate("el => getComputedStyle(el).borderRadius")
        presentation_status_height = page.locator('.statusbar').evaluate("el => getComputedStyle(el).height")
        presentation_edges = page.locator('.workspace').evaluate("el => { const panel=el.querySelector('.slide-list').getBoundingClientRect(); const stage=el.querySelector('.stage-wrap').getBoundingClientRect(); return [panel.right, stage.left]; }")

        page.set_content("""<!doctype html><style>{}</style><body class='office-product office-pdf'>
          <main class='viewer-app'><header class='titlebar'></header><div class='commandbar'></div><div class='workspace-body'></div>
          <footer class='statusbar'><span class='pdf-save-note'>Private local note</span></footer></main>
        </body>""".format(PDF_CSS))
        pdf_title_top = page.locator('.titlebar').evaluate("el => el.getBoundingClientRect().top")
        pdf_status_bottom = page.locator('.statusbar').evaluate("el => el.getBoundingClientRect().bottom")
        pdf_status_height = page.locator('.statusbar').evaluate("el => getComputedStyle(el).height")
        pdf_note_display = page.locator('.pdf-save-note').evaluate("el => getComputedStyle(el).display")
        browser.close()

    result = {
        "desktop_columns": desktop_cols,
        "phone_columns": phone_cols,
        "card_radius": card_radius,
        "documents_icon_preserved": "documents.svg" in document_icon,
        "titlebar_min_height": title_height,
        "documents_accent": doc_accent,
        "epub_accent": epub_accent,
        "sheets_title_display": sheets_title_display,
        "sheets_title_position": sheets_title_position,
        "sheets_footer_height": sheets_footer_height,
        "presentation_panel_shadow": presentation_panel_shadow,
        "presentation_panel_radius": presentation_panel_radius,
        "presentation_status_height": presentation_status_height,
        "presentation_edges": presentation_edges,
        "pdf_title_top": pdf_title_top,
        "pdf_status_bottom": pdf_status_bottom,
        "pdf_status_height": pdf_status_height,
        "pdf_note_display": pdf_note_display,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert desktop_cols == 3, result
    assert phone_cols == 1, result
    assert "documents.svg" in document_icon, result
    assert title_height == "44px", result
    assert doc_accent == "#2f6fed", result
    assert epub_accent == "#7655c7", result
    assert sheets_title_display == "grid", result
    assert sheets_title_position == "static", result
    assert sheets_footer_height == "34px", result
    assert presentation_panel_shadow == "none", result
    assert presentation_panel_radius == "0px", result
    assert presentation_status_height == "34px", result
    assert abs(presentation_edges[0] - presentation_edges[1]) < 0.5, result
    assert abs(pdf_title_top) < 0.5, result
    assert abs(pdf_status_bottom - 800) < 0.5, result
    assert pdf_status_height == "34px", result
    assert pdf_note_display == "none", result
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
