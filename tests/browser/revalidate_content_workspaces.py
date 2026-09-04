#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "tests" / "browser" / "results" / "content_workspaces_visual_02031.json"


def read_css(*relatives: str) -> str:
    return "\n".join((ROOT / relative).read_text(encoding="utf-8") for relative in relatives)


SHARED = read_css(
    "shared/office-shell.css",
    "shared/ui/design-tokens.css",
    "shared/ui/components.css",
    "shared/ui/workspace-layout.css",
    "shared/ui/visual-foundation.css",
    "shared/ui/visual.css",
    "shared/ui/content.css",
    "shared/ui/workspace.css",
)
DOCUMENTS = read_css("apps/documents/styles.css") + "\n" + SHARED
TXT = read_css("apps/txt/styles.css") + "\n" + SHARED
EPUB = read_css("apps/epub/styles.css") + "\n" + SHARED


def px(page, selector: str, property_name: str) -> str:
    return page.locator(selector).evaluate(
        "(el, prop) => getComputedStyle(el).getPropertyValue(prop).trim()",
        property_name,
    )


def main() -> int:
    browser_name = os.environ.get("INKDOS_BROWSER", "chromium").strip().lower()
    with sync_playwright() as p:
        launcher = getattr(p, browser_name)
        launch_kwargs = {}
        executable = (
            os.environ.get("CHROMIUM_PATH")
            or os.environ.get("INKDOS_BROWSER_EXECUTABLE", "")
        ).strip()
        if executable and browser_name == "chromium":
            launch_kwargs["executable_path"] = executable
            launch_kwargs["args"] = ["--no-sandbox"]
        browser = launcher.launch(headless=True, **launch_kwargs)
        page = browser.new_page(viewport={"width": 1180, "height": 800})

        page.set_content(f"""<!doctype html><style>{DOCUMENTS}</style>
        <body class='office-product office-documents'>
          <div class='app-shell'>
            <header class='topbar'><div class='left-tools'><button class='icon-btn'>A</button></div><div class='document-title'><span class='word-badge'>W</span><input class='title-input' value='Draft.docx'></div><div class='right-tools'><button id='saveBtn' class='icon-btn'>S</button></div></header>
            <div class='formatbar'><select><option>Normal</option></select><button class='fmt-btn'>B</button></div>
            <div class='ruler'><div class='ruler-track'></div></div>
            <div class='workspace'><aside class='sidebar'><div class='sidebar-tabs'><button class='tab active'>Pages</button></div></aside><main class='viewport'><div class='pages-host'><article class='page'></article></div></main></div>
            <footer class='statusbar'>Ready</footer>
          </div>
        </body>""")
        docs_toolbar_height = px(page, ".formatbar", "min-height")
        docs_grid = px(page, ".workspace", "grid-template-columns")
        docs_page_shadow = px(page, ".page", "box-shadow")
        docs_save_background = px(page, "#saveBtn", "background-color")
        page.set_viewport_size({"width": 700, "height": 800})
        docs_mobile_grid = px(page, ".workspace", "grid-template-columns")

        page.set_viewport_size({"width": 1180, "height": 800})
        page.set_content(f"""<!doctype html><style>{TXT}</style>
        <body class='office-product office-txt'>
          <header class='txt-titlebar'><div class='title-actions'></div><div class='title-center'><input class='file-title-input'></div><div class='title-actions'></div></header>
          <div class='txt-toolbar'><button class='tool-btn active'>Wrap</button><label class='font-size-control'><span>Text size</span><select><option>16</option></select></label></div>
          <main class='txt-main'><section class='editor-shell'><textarea id='editor'></textarea></section></main>
          <footer class='txt-statusbar'><span>Ready</span><span class='status-spacer'></span><span>1 line</span><span>0 words</span></footer>
        </body>""")
        txt_toolbar_height = px(page, ".txt-toolbar", "min-height")
        txt_editor_radius = px(page, ".editor-shell", "border-radius")
        txt_editor_shadow = px(page, ".editor-shell", "box-shadow")
        txt_status_height = px(page, ".txt-statusbar", "height")
        page.set_viewport_size({"width": 390, "height": 780})
        txt_mobile_radius = px(page, ".editor-shell", "border-radius")

        page.set_viewport_size({"width": 1180, "height": 800})
        page.set_content(f"""<!doctype html><style>{EPUB}</style>
        <body class='office-product office-epub' data-reader-theme='paper'>
          <header class='epub-titlebar'></header>
          <div class='reader-toolbar'><div class='size-controls'><button class='tool-btn'>A−</button><span id='fontSizeLabel'>18 px</span><button class='tool-btn'>A+</button></div><div class='theme-controls'><button class='theme-dot active' data-theme='paper'></button></div></div>
          <main class='reader-main'><section class='reader-shell'><button class='page-arrow'>‹</button><article class='page-surface'><div class='page-content'><h1>Chapter</h1><p>Reading sample.</p></div></article><button class='page-arrow'>›</button></section></main>
          <footer class='reader-statusbar'>Ready</footer>
        </body>""")
        epub_toolbar_height = px(page, ".reader-toolbar", "min-height")
        epub_surface_radius = px(page, ".page-surface", "border-radius")
        epub_arrow_size = (
            px(page, ".page-arrow:first-child", "width"),
            px(page, ".page-arrow:first-child", "height"),
        )
        epub_grid = px(page, ".reader-shell", "grid-template-columns")
        epub_status_height = px(page, ".reader-statusbar", "height")
        page.set_viewport_size({"width": 390, "height": 780})
        epub_mobile_radius = px(page, ".page-surface", "border-radius")
        browser.close()

    result = {
        "documents_toolbar_min_height": docs_toolbar_height,
        "documents_grid": docs_grid,
        "documents_mobile_grid": docs_mobile_grid,
        "documents_page_shadow_present": docs_page_shadow != "none",
        "documents_save_emphasized": docs_save_background != "rgba(0, 0, 0, 0)",
        "txt_toolbar_min_height": txt_toolbar_height,
        "txt_editor_radius": txt_editor_radius,
        "txt_mobile_radius": txt_mobile_radius,
        "txt_editor_shadow_present": txt_editor_shadow != "none",
        "txt_status_height": txt_status_height,
        "epub_toolbar_min_height": epub_toolbar_height,
        "epub_surface_radius": epub_surface_radius,
        "epub_mobile_radius": epub_mobile_radius,
        "epub_arrow_size": epub_arrow_size,
        "epub_grid": epub_grid,
        "epub_status_height": epub_status_height,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    assert docs_toolbar_height == "40px", result
    assert docs_grid.split()[0] == "238px", result
    assert docs_mobile_grid.split()[0] == "200px", result
    assert result["documents_page_shadow_present"], result
    assert result["documents_save_emphasized"], result
    assert txt_toolbar_height == "40px", result
    assert txt_status_height == "34px", result
    assert txt_editor_radius == "12px", result
    assert txt_mobile_radius == "12px", result
    assert result["txt_editor_shadow_present"], result
    assert epub_toolbar_height == "40px", result
    assert epub_status_height == "34px", result
    assert epub_surface_radius == "12px", result
    assert epub_mobile_radius == "12px", result
    assert epub_arrow_size == ("40px", "40px"), result
    assert epub_grid.split()[0] == "44px", result
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
