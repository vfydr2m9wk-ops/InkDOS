#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "tests" / "browser" / "results" / "workspace_unification_02031.json"


def read_css(*paths: str) -> str:
    return "\n".join((ROOT / path).read_text(encoding="utf-8") for path in paths)


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


def rect(page, selector: str):
    return page.locator(selector).evaluate("el => { const r=el.getBoundingClientRect(); return [r.left,r.top,r.right,r.bottom,r.width,r.height]; }")


def main() -> int:
    browser_name = os.environ.get("INKDOS_BROWSER", "chromium").strip().lower()
    with sync_playwright() as p:
        launcher = getattr(p, browser_name)
        kwargs = {}
        executable = (os.environ.get("CHROMIUM_PATH") or os.environ.get("INKDOS_BROWSER_EXECUTABLE", "")).strip()
        if executable and browser_name == "chromium":
            kwargs["executable_path"] = executable
            kwargs["args"] = ["--no-sandbox"]
        browser = launcher.launch(headless=True, **kwargs)
        page = browser.new_page(viewport={"width": 1024, "height": 720})

        sheets_css = read_css("apps/spreadsheets/styles.css") + "\n" + SHARED
        page.set_content(f"""<!doctype html><style>{sheets_css}</style><body class='office-product office-spreadsheets'>
          <header class='titlebar'><div class='left'><button class='icon-btn'>H</button></div><div class='document-title'><input class='title-input' value='Book.xlsx'></div><div class='right'><button class='icon-btn'>S</button></div></header>
          <section class='toolbar'><span class='viewer-label'>InkDOS 0.20.3.1</span></section><section class='formula-row'></section><main></main>
          <footer><div id='sheetTabs'></div><div class='status'><span>Ready</span><div class='zoom-controls'><button>−</button><input type='range'><button>+</button><button id='fitWidth'>Fit</button><span id='zoomLabel'>100%</span></div></div></footer>
        </body>""")
        sheets_footer = rect(page, "footer")
        sheets_title = rect(page, ".titlebar")
        sheets_slider = rect(page, ".zoom-controls input")
        sheets_viewer_label = page.locator('.viewer-label').evaluate("el => getComputedStyle(el).display")

        pres_css = read_css("apps/presentations/styles.css") + "\n" + SHARED
        page.set_content(f"""<!doctype html><style>{pres_css}</style><body class='office-product office-presentations'>
          <main class='app hide-notes'><header class='titlebar'><div class='titlebar-left'></div><input class='presentation-title-input'><div class='titlebar-right'><button class='top-action present-top-action'><span>Current</span></button></div></header><nav class='toolbar'></nav><section class='tools'></section>
          <section class='workspace hide-inspector'><aside class='slide-list'></aside><section class='stage-wrap'></section><aside class='inspector'></aside></section><section class='notes-panel'></section>
          <footer class='statusbar'><span>Slide 1</span><span class='grow'></span><div class='bottom-zoom'><button>−</button><input type='range'><button>+</button><button>Fit</button><span id='zoomText'>100%</span></div></footer></main>
        </body>""")
        slide_edge = rect(page, ".slide-list")[2]
        stage_edge = rect(page, ".stage-wrap")[0]
        pres_footer = rect(page, ".statusbar")
        pres_top_label = page.locator('.present-top-action span').evaluate("el => getComputedStyle(el).display")

        pdf_css = read_css("apps/pdf/styles.css") + "\n" + SHARED
        page.set_content(f"""<!doctype html><style>{pdf_css}</style><body class='office-product office-pdf'>
          <main class='viewer-app'><header class='titlebar'><div class='left-tools'></div><div class='document-title'>Doc.pdf</div><div class='right-tools'></div></header>
          <div class='commandbar'><div class='command-group'><button class='tool-btn'>A</button><button class='tool-btn'>B</button></div></div>
          <div class='workspace-body'><aside class='sidebar'></aside><section class='viewer-stage'></section></div>
          <footer class='statusbar'><span>Ready</span><span class='status-spacer'></span><div class='pdf-bottom-nav'><div class='page-controls'></div><div class='pdf-bottom-zoom'><button>−</button><input type='range'><button>+</button><button>Fit</button><span id='pdfZoomLabel'>100%</span></div></div></footer></main>
        </body>""")
        pdf_sidebar_edge = rect(page, ".sidebar")[2]
        pdf_sidebar_style = page.locator(".sidebar").evaluate("el => ({width:getComputedStyle(el).width,maxWidth:getComputedStyle(el).maxWidth,minWidth:getComputedStyle(el).minWidth,position:getComputedStyle(el).position})")
        pdf_stage_edge = rect(page, ".viewer-stage")[0]
        pdf_toolbar = rect(page, ".commandbar")
        pdf_group = rect(page, ".commandbar .command-group")
        pdf_footer = rect(page, ".statusbar")

        epub_css = read_css("apps/epub/styles.css") + "\n" + SHARED
        page.set_content(f"""<!doctype html><style>{epub_css}</style><body class='office-product office-epub'>
          <header class='epub-titlebar'><div class='title-actions'><button class='icon-btn'>H</button></div><div class='title-center'><img class='epub-app-icon'><input class='file-title-input'></div><div class='title-actions title-actions-right'></div></header>
          <div class='reader-toolbar'><div class='size-controls'></div><div class='theme-controls'><button class='theme-dot active'></button><button class='theme-dot'></button></div></div><main class='reader-main'></main>
          <footer class='reader-statusbar'><span>Ready</span><span class='status-spacer'></span><div class='workspace-zoom'><button>−</button><input type='range'><button>+</button><button>Fit</button><span id='epubZoomLabel'>100%</span></div></footer>
        </body>""")
        epub_toolbar = rect(page, ".reader-toolbar")
        epub_dot = rect(page, ".theme-dot:first-of-type")
        epub_theme_bg = page.locator('.theme-controls').evaluate("el => getComputedStyle(el).backgroundColor")

        page.set_viewport_size({"width": 1920, "height": 900})
        title_button = rect(page, ".epub-titlebar .icon-btn")
        wide_title = rect(page, ".epub-titlebar")
        browser.close()

    result = {
        "sheets_footer": sheets_footer,
        "sheets_title": sheets_title,
        "sheets_slider": sheets_slider,
        "sheets_viewer_label": sheets_viewer_label,
        "presentation_edges": [slide_edge, stage_edge],
        "presentation_footer": pres_footer,
        "presentation_top_label": pres_top_label,
        "pdf_edges": [pdf_sidebar_edge, pdf_stage_edge],
        "pdf_sidebar_style": pdf_sidebar_style,
        "pdf_toolbar": pdf_toolbar,
        "pdf_group": pdf_group,
        "pdf_footer": pdf_footer,
        "epub_toolbar": epub_toolbar,
        "epub_dot": epub_dot,
        "epub_theme_background": epub_theme_bg,
        "wide_title_button": title_button,
        "wide_title": wide_title,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    assert abs(sheets_footer[3] - 720) < 0.5 and abs(sheets_footer[5] - 34) < 0.5, result
    assert abs(sheets_title[5] - 44) < 0.5, result
    assert sheets_slider[4] >= 100, result
    assert sheets_viewer_label == 'none', result
    assert abs(slide_edge - stage_edge) < 0.5 and abs(slide_edge - 188) < 0.5, result
    assert pres_top_label == 'none', result
    assert abs(pres_footer[3] - 720) < 0.5 and abs(pres_footer[5] - 34) < 0.5, result
    assert abs(pdf_sidebar_edge - pdf_stage_edge) < 0.5 and pdf_sidebar_style['width'] == '238px', result
    assert abs((pdf_group[0] + pdf_group[2]) / 2 - 512) < 2, result
    assert abs(pdf_footer[3] - 720) < 0.5 and abs(pdf_footer[5] - 34) < 0.5, result
    assert abs(epub_toolbar[5] - 40) < 0.5, result
    assert abs(epub_dot[4] - 18) < 0.5 and abs(epub_dot[5] - 18) < 0.5, result
    assert epub_theme_bg in ("rgba(0, 0, 0, 0)", "transparent"), result
    assert abs(title_button[4] - 32) < 0.5 and abs(title_button[5] - 32) < 0.5, result
    assert abs(wide_title[5] - 44) < 0.5, result
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
