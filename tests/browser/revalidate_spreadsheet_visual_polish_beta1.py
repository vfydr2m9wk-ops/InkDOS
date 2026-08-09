#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "tests" / "browser" / "results" / "spreadsheet_visual_polish_beta1.json"


def read_css(*paths: str) -> str:
    return "\n".join((ROOT / path).read_text(encoding="utf-8") for path in paths)


CSS = read_css(
    "apps/spreadsheets/styles.css",
    "shared/office-shell.css",
    "shared/ui/design-tokens.css",
    "shared/ui/components.css",
    "shared/ui/workspace-layout.css",
    "shared/ui/visual-foundation.css",
    "shared/ui/visual-foundation-v0203.css",
    "shared/ui/content-workspaces-v02031.css",
    "shared/ui/workspace-unification-v02031.css",
    "shared/ui/spreadsheets-beta1-polish.css",
)


def px(page, selector: str, prop: str) -> float:
    value = page.locator(selector).evaluate(f"el => getComputedStyle(el).{prop}")
    return float(str(value).replace("px", ""))


def style(page, selector: str, prop: str) -> str:
    return page.locator(selector).evaluate(f"el => getComputedStyle(el).{prop}")


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
        page = browser.new_page(viewport={"width": 1180, "height": 760})
        page.set_content(f"""<!doctype html><style>{CSS}</style><body class='office-product office-spreadsheets sheet-view'>
          <header class='titlebar'><div class='left'></div><div class='document-title'><input class='title-input' value='Book.xlsx'></div><div class='right'></div></header>
          <section class='toolbar'><button class='active-format'>B</button><button class='gridlines-toggle active'>Gridlines</button></section>
          <section class='formula-row'><input id='nameBox' value='A1'><span class='fx'>fx</span><div class='formula-editor'><input id='formulaInput' value='=SUM(A1:A3)'></div><button id='addFormulaRangeBtn'>+ Range</button></section>
          <main><div id='gridViewport'><div id='grid'><div class='corner'></div><div class='col-header axis-active'>A</div><div class='row-header axis-active'>1</div><div class='cell selected in-range'>42</div><div class='cell in-range'>7</div></div></div></main>
          <footer><div id='sheetTabs'><button class='active'>Summary</button><button>Data</button><button id='addSheetBtn'>+</button><button id='deleteSheetBtn'>−</button></div><div class='status'><span id='selectionStats'>Average: 24.5 · Sum: 49</span><div class='zoom-controls'><button>−</button><input type='range'><button>+</button><button>Fit</button><span>100%</span></div></div></footer>
        </body>""")

        desktop = {
            "formula_height": px(page, ".formula-row", "height"),
            "name_width": px(page, "#nameBox", "width"),
            "fx_width": px(page, ".formula-row .fx", "width"),
            "selected_outline": style(page, ".cell.selected", "outlineWidth"),
            "add_position": style(page, "#addSheetBtn", "position"),
            "add_right": style(page, "#addSheetBtn", "right"),
            "delete_position": style(page, "#deleteSheetBtn", "position"),
            "delete_right": style(page, "#deleteSheetBtn", "right"),
            "footer_height": px(page, "footer", "height"),
        }
        page.set_viewport_size({"width": 700, "height": 760})
        compact = {
            "name_width": px(page, "#nameBox", "width"),
            "fx_width": px(page, ".formula-row .fx", "width"),
            "stats_max_width": style(page, "#selectionStats", "maxWidth"),
        }
        browser.close()

    result = {"desktop": desktop, "compact": compact}
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    assert abs(desktop["formula_height"] - 40) < 0.5, result
    assert abs(desktop["name_width"] - 74) < 0.5, result
    assert abs(desktop["fx_width"] - 28) < 0.5, result
    assert desktop["selected_outline"] == "2px", result
    assert desktop["add_position"] == "sticky" and desktop["add_right"] == "34px", result
    assert desktop["delete_position"] == "sticky" and desktop["delete_right"] == "0px", result
    assert abs(desktop["footer_height"] - 34) < 0.5, result
    assert abs(compact["name_width"] - 58) < 0.5, result
    assert abs(compact["fx_width"] - 26) < 0.5, result
    assert compact["stats_max_width"] == "110px", result
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
