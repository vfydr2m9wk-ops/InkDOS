#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "tests" / "browser" / "results" / "ui_correction_02031.json"


def read_css(*paths: str) -> str:
    return "\n".join((ROOT / path).read_text(encoding="utf-8") for path in paths)


SHARED = read_css(
    "shared/office-shell.css",
    "shared/ui/design-tokens.css",
    "shared/ui/components.css",
    "shared/ui/workspace-layout.css",
    "shared/ui/visual-foundation.css",
    "shared/ui/visual-foundation-v0203.css",
    "shared/ui/content-workspaces-v02031.css",
    "shared/ui/workspace-unification-v02031.css",
)


def rect(page, selector: str):
    return page.locator(selector).evaluate(
        "el => { const r=el.getBoundingClientRect(); return [r.left,r.top,r.right,r.bottom,r.width,r.height]; }"
    )


def main() -> int:
    browser_name = os.environ.get("INKDESK_BROWSER", "chromium").strip().lower()
    with sync_playwright() as p:
        launcher = getattr(p, browser_name)
        kwargs = {}
        executable = (os.environ.get("CHROMIUM_PATH") or os.environ.get("INKDESK_BROWSER_EXECUTABLE", "")).strip()
        if executable and browser_name == "chromium":
            kwargs["executable_path"] = executable
            kwargs["args"] = ["--no-sandbox"]
        browser = launcher.launch(headless=True, **kwargs)
        page = browser.new_page(viewport={"width": 1024, "height": 720})

        sheets_css = read_css("apps/spreadsheets/styles.css") + "\n" + SHARED
        page.set_content(f"""<!doctype html><style>{sheets_css}</style><body class='office-product office-spreadsheets'>
          <header class='titlebar'><div class='left'></div><div class='document-title'><input class='title-input'></div><div class='right'></div></header>
          <section class='toolbar'></section><section class='formula-row'></section><main></main>
          <footer><div id='sheetTabs'><button class='active'>Sheet1</button><button id='addSheetBtn'>+</button></div><div class='status'><span>Ready</span><div class='zoom-controls'><button>−</button><input type='range'><button>+</button><button>Fit</button><span>100%</span></div></div></footer>
        </body>""")
        sheet_footer = rect(page, "footer")
        sheet_tab = rect(page, "#sheetTabs .active")
        add_sheet = rect(page, "#addSheetBtn")
        add_visible = page.locator("#addSheetBtn").evaluate("el => getComputedStyle(el).display !== 'none'")

        pdf_css = read_css("apps/pdf/styles.css") + "\n" + SHARED
        page.set_content(f"""<!doctype html><style>{pdf_css}</style><body class='office-product office-pdf'>
          <main class='viewer-app'><header class='titlebar'><div class='left-tools'></div><div class='document-title'>Doc.pdf</div><div class='right-tools'></div></header>
          <div class='commandbar'><div class='command-group'><button class='tool-btn'>A</button></div></div>
          <div class='workspace-body'><aside class='sidebar'><div class='sidebar-tabs'><button class='sidebar-tab active'>Pages</button><button class='sidebar-tab'>Index</button><button class='sidebar-tab'>Bookmarks</button><button class='sidebar-tab'>Comments</button></div><div class='sidebar-content'></div></aside><section class='viewer-stage'></section></div>
          <footer class='statusbar'></footer></main>
        </body>""")
        pdf_sidebar = rect(page, ".sidebar")
        pdf_tabs_fit = page.locator(".sidebar-tabs").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
        pdf_tab_overflow = page.locator(".sidebar-tab").evaluate_all("els => els.map(el => [el.textContent, el.scrollWidth, el.clientWidth])")

        pres_css = read_css("apps/presentations/styles.css") + "\n" + SHARED
        page.set_content(f"""<!doctype html><style>{pres_css}</style><body class='office-product office-presentations'>
          <main class='app hide-notes'><header class='titlebar'><div class='titlebar-left'></div><input class='presentation-title-input'><div class='titlebar-right'><button class='top-action present-top-action'><svg><rect x='3' y='4' width='17' height='12'/><path d='M9 7 15 10 9 13z'/></svg><span>Current</span></button></div></header><nav class='toolbar'></nav>
          <section class='tools hidden' id='toolsView'><button id='togglePresentationsBtn'>Hide thumbnails</button><button id='presentViewBtn'>Present current</button><span class='sep'></span><button id='zoomOutBtn'>−</button><input id='zoomRange' type='range'><button id='zoomInBtn'>+</button><button id='fitBtn'>Fit</button></section>
          <section class='workspace hide-inspector'><aside class='slide-list'></aside><section class='stage-wrap'></section><aside class='inspector'></aside></section><section class='notes-panel'></section><footer class='statusbar'><div class='bottom-zoom'><button>−</button><input type='range'><button>+</button><button>Fit</button><span>100%</span></div></footer></main>
        </body>""")
        top_zoom_displays = page.locator("#zoomOutBtn,#zoomRange,#zoomInBtn,#fitBtn").evaluate_all("els => els.map(el => getComputedStyle(el).display)")
        bottom_zoom_display = page.locator(".bottom-zoom").evaluate("el => getComputedStyle(el).display")
        present_svg = page.locator(".present-top-action svg").evaluate("el => ({fill:getComputedStyle(el).fill,stroke:getComputedStyle(el).stroke})")

        launcher_css = read_css("shared/hub.css", "shared/ui/visual-foundation-v0203.css")
        page.set_viewport_size({"width": 1180, "height": 820})
        page.set_content(f"""<!doctype html><style>{launcher_css}</style><body><main class='hub-shell'><section class='workspace-grid'>
          <a class='workspace-card documents'><span class='app-icon'></span><span class='open-arrow'>›</span><span class='workspace-copy'><strong>Documents</strong><small>Create, edit and save DOCX copies locally.</small></span></a>
        </section></main></body>""")
        landscape_icon = rect(page, ".app-icon")
        landscape_copy = rect(page, ".workspace-copy")
        landscape_arrow = rect(page, ".open-arrow")
        page.set_viewport_size({"width": 390, "height": 844})
        phone_icon = rect(page, ".app-icon")
        phone_copy = rect(page, ".workspace-copy")
        phone_arrow = rect(page, ".open-arrow")

        result = {
            "sheet_footer": sheet_footer,
            "sheet_tab": sheet_tab,
            "add_sheet": add_sheet,
            "add_visible": add_visible,
            "pdf_sidebar": pdf_sidebar,
            "pdf_tabs_fit": pdf_tabs_fit,
            "pdf_tab_overflow": pdf_tab_overflow,
            "top_zoom_displays": top_zoom_displays,
            "bottom_zoom_display": bottom_zoom_display,
            "present_svg": present_svg,
            "launcher_landscape": [landscape_icon, landscape_copy, landscape_arrow],
            "launcher_phone": [phone_icon, phone_copy, phone_arrow],
        }
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")

        assert abs(sheet_footer[3] - 720) < .5 and abs(sheet_footer[5] - 34) < .5, result
        assert sheet_tab[5] <= 33.5 and add_sheet[5] <= 33.5 and add_visible, result
        assert abs(pdf_sidebar[4] - 238) < .5 and pdf_tabs_fit, result
        assert all(scroll <= client + 1 for _, scroll, client in pdf_tab_overflow), result
        assert all(display == "none" for display in top_zoom_displays), result
        assert bottom_zoom_display == "flex", result
        assert present_svg["fill"] in ("none", "rgba(0, 0, 0, 0)"), result
        assert landscape_icon[2] <= landscape_copy[0] and landscape_copy[2] <= landscape_arrow[0], result
        assert phone_icon[2] <= phone_copy[0] and phone_copy[2] <= phone_arrow[0], result
        browser.close()
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
