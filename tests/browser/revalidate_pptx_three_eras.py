#!/usr/bin/env python3
"""Optional browser round-trip validation for the three PPT/PPTX eras."""
from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
import sys

try:
    from bs4 import BeautifulSoup
    from playwright.sync_api import sync_playwright
except ImportError as exc:
    raise SystemExit("Install beautifulsoup4 and playwright to run this optional test") from exc

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "compatibility-fixtures" / "presentations"
OUT = ROOT / "tests" / "browser" / "results" / "pptx"
OUT.mkdir(parents=True, exist_ok=True)


def load_app(page) -> None:
    soup = BeautifulSoup((ROOT / "apps/presentations/index.html").read_text(encoding="utf-8"), "html.parser")
    for item in soup.find_all(["script", "link"]):
        item.decompose()
    base = soup.new_tag("base", href=ROOT.as_uri() + "/")
    if soup.head:
        soup.head.insert(0, base)
    page.set_content(str(soup), wait_until="domcontentloaded")
    for path in (ROOT / "apps/presentations/styles.css", ROOT / "shared/office-shell.css"):
        page.add_style_tag(path=str(path))
    for path in (
        ROOT / "shared/office-runtime.js",
                ROOT / "shared/vendor/jszip.min.js",
        ROOT / "apps/presentations/engine/compatibility.js",
        ROOT / "shared/office-shell.js",
        ROOT / "apps/presentations/app.js",
    ):
        page.add_script_tag(path=str(path))


def state(page):
    return page.evaluate(
        """() => { const p=window.__LocalPresentationsDebug.getPresentation(); return {
        slides:p.slides.map(s=>({notes:s.notes,transition:s.transition,objects:s.objects.map(o=>({type:o.type,text:o.text||'',sourceLayer:o.sourceLayer||'',chartPath:o.chartPath||'',categories:o.categories||[],series:o.series||[],cropZoom:o.cropZoom||1}))}))}; }"""
    )


def goto_slide(page, index: int) -> None:
    page.evaluate("i=>document.querySelectorAll('#slideList .thumb')[i].click()", index)
    page.wait_for_timeout(120)


def edit_first_title(page, marker: str) -> None:
    goto_slide(page, 0)
    object_id = page.evaluate(
        """() => {const p=window.__LocalPresentationsDebug.getPresentation();const o=p.slides[0].objects.find(x=>x.type==='text'&&x.sourceLayer==='slide'&&!x.templateObject);return o&&o.id}"""
    )
    page.evaluate(
        "(id)=>document.querySelector('#slideCanvas [data-id=\"'+id+'\"]').dispatchEvent(new MouseEvent('dblclick',{bubbles:true}))",
        object_id,
    )
    editor = page.locator(f'#slideCanvas [data-id="{object_id}"] .editable[contenteditable="true"]')
    editor.fill(editor.inner_text() + "\n" + marker)
    page.evaluate("(id)=>document.querySelector('#slideCanvas [data-id=\"'+id+'\"] .editable').blur()", object_id)


def save(page, destination: Path) -> None:
    with page.expect_download(timeout=30_000) as download:
        page.click("#saveBtn")
    download.value.save_as(str(destination))


def content_hashes(path: Path) -> dict[str, str]:
    with ZipFile(path) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if not name.endswith("/")}


def package_info(path: Path) -> dict[str, object]:
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        slides = [archive.read(name).decode("utf-8", "replace") for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        return {
            "part_count": len(names),
            "chart": "ppt/charts/chart1.xml" in names,
            "notes": any(name.startswith("ppt/notesSlides/") and name.endswith(".xml") for name in names),
            "media": any(name.startswith("ppt/media/") for name in names),
            "table": any("<a:tbl" in xml for xml in slides),
            "transition": any("<p:transition" in xml for xml in slides),
        }


def main() -> int:
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, details=None) -> None:
        checks.append({"name": name, "passed": bool(passed), "details": details})
        if not passed:
            raise AssertionError(f"{name}: {details}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])

        page = browser.new_page()
        dialogs: list[str] = []
        page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
        load_app(page)
        page.set_input_files("#fileInput", str(FIXTURES / "era1_office_97_2003_legacy.ppt"))
        page.wait_for_timeout(400)
        check("legacy PPT rejection", any("Legacy PPT files" in message for message in dialogs), dialogs)
        page.close()

        for era in ("era2_office_2007_2013_baseline.pptx", "era3_office_2016_365_modern.pptx"):
            source = FIXTURES / era
            exported = OUT / era.replace(".pptx", ".exported.pptx")
            page = browser.new_page(accept_downloads=True, viewport={"width": 1400, "height": 900})
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("dialog", lambda dialog: dialog.accept())
            load_app(page)
            page.set_input_files("#fileInput", str(source))
            page.wait_for_function("window.__LocalPresentationsDebug && window.__LocalPresentationsDebug.getPresentation()")
            before = state(page)
            if era.startswith("era2"):
                goto_slide(page, 2)
                check("baseline image", page.locator("#slideCanvas .obj.image").count() > 0, before)
                check("baseline table", page.locator("#slideCanvas .obj.table").count() > 0, before)
            else:
                check("modern notes", before["slides"][0]["notes"] == "MODERN-NOTES-MARKER", before)
                check("modern transition", before["slides"][0]["transition"]["type"] == "fade", before)
                goto_slide(page, 1)
                check("modern image", page.locator("#slideCanvas .obj.image").count() > 0, state(page))
                check("modern chart", page.locator("#slideCanvas .obj.chart").count() > 0, state(page))
            edit_first_title(page, "PPTX-ROUNDTRIP-0185")
            page.click("#undoBtn")
            check(f"{era}: text edit undo", "PPTX-ROUNDTRIP-0185" not in str(state(page)), state(page))
            page.click("#redoBtn")
            check(f"{era}: text edit redo", "PPTX-ROUNDTRIP-0185" in str(state(page)), state(page))
            save(page, exported)
            page.close()

            original_hashes, exported_hashes = content_hashes(source), content_hashes(exported)
            check(f"{era}: all original parts", set(original_hashes) <= set(exported_hashes), sorted(set(original_hashes) - set(exported_hashes)))
            info = package_info(exported)
            check(f"{era}: table retained", bool(info["table"]), info)
            if era.startswith("era3"):
                check("modern advanced parts retained", bool(info["chart"] and info["notes"] and info["media"] and info["transition"]), info)
            check(f"{era}: no runtime errors", not errors, errors)

        browser.close()

    result = {"checks": checks, "passed": sum(bool(item["passed"]) for item in checks), "total": len(checks)}
    (OUT / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
