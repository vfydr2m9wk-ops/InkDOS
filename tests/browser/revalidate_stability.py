"""Browser-level stabilization gate that avoids localhost/file navigation.

The test builds each relevant workspace with set_content and injects repository
assets directly. That keeps the regression executable in locked-down runners
while still exercising real DOM/runtime behavior in Chromium.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from pypdf import PdfWriter

from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def shell_html(relative: str) -> str:
    soup = BeautifulSoup(text(relative), "html.parser")
    for node in soup.find_all("script"):
        node.decompose()
    for node in soup.find_all("link"):
        node.decompose()
    return str(soup)


def add_styles(page, relatives):
    for relative in relatives:
        page.add_style_tag(content=text(relative))


def add_scripts(page, relatives):
    for relative in relatives:
        page.add_script_tag(content=text(relative))


def check(value, message):
    if not value:
        raise RuntimeError(message)


def make_long_pdf(path: Path, pages: int = 20):
    writer = PdfWriter()
    for index in range(pages):
        portrait = index % 2 == 0
        writer.add_blank_page(
            width=612 if portrait else 792,
            height=792 if portrait else 612,
        )
    with path.open("wb") as handle:
        writer.write(handle)


def main():
    report = {"browser": requested_browser_name(), "passed": False, "checks": []}
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        try:
            context = browser.new_context(
                viewport={"width": 1280, "height": 820}, color_scheme="dark"
            )
            page = context.new_page()
            page.set_default_timeout(30000)

            # Light-only must win after the retained Spreadsheet beta-1 polish.
            page.set_content(
                '<html><body class="office-product office-spreadsheets"><div>x</div></body></html>'
            )
            add_styles(
                page,
                [
                    "apps/spreadsheets/styles.css",
                    "shared/ui/polish.css",
                ],
            )
            sheet = page.evaluate(
                """() => ({
                    scheme:getComputedStyle(document.documentElement).colorScheme,
                    cell:getComputedStyle(document.body).getPropertyValue('--cell').trim(),
                    text:getComputedStyle(document.body).getPropertyValue('--text').trim(),
                    bg:getComputedStyle(document.body).getPropertyValue('--bg').trim()
                })"""
            )
            check(
                "light" in sheet["scheme"]
                and sheet["cell"] == "#fff"
                and sheet["text"] == "#20242a"
                and sheet["bg"] == "#edf0f4",
                f"light-only spreadsheet contract failed: {sheet}",
            )
            report["checks"].append("spreadsheet light-only palette under dark host")

            # Collapsed desktop Format panel must physically leave the grid.
            page.set_content(
                '<html><body class="office-product office-presentations">'
                '<section class="workspace hide-inspector"><aside class="slide-list"></aside>'
                '<section class="stage-wrap"></section><aside id="inspector" class="inspector">Format</aside>'
                "</section></body></html>"
            )
            add_styles(page, ["apps/presentations/styles.css", "apps/presentations/stability.css"])
            layout = page.evaluate(
                """() => {
                    const w=document.querySelector('.workspace'),i=document.querySelector('#inspector');
                    return {columns:getComputedStyle(w).gridTemplateColumns,
                            width:i.getBoundingClientRect().width,
                            display:getComputedStyle(i).display};
                }"""
            )
            check(
                layout["display"] == "none" and layout["width"] == 0,
                f"inspector still occupies space: {layout}",
            )
            check(
                len(layout["columns"].split()) == 2,
                f"third presentation grid track remains: {layout}",
            )
            report["checks"].append("presentation hidden format panel occupies zero desktop space")

            # Run the actual Presentation runtime without network navigation and
            # verify that a common editing operation now enables Undo/Redo.
            page.set_content(shell_html("apps/presentations/index.html"))
            add_styles(
                page,
                [
                    "apps/presentations/styles.css",
                    "shared/ui/polish.css",
                    "apps/presentations/stability.css",
                ],
            )
            add_scripts(
                page,
                [
                    "shared/office-runtime.js",
                    "shared/vendor/jszip.min.js",
                    "apps/presentations/engine/compatibility.js",
                    "apps/presentations/engine/background-resolver.js",
                    "shared/local-recovery.js",
                    "apps/presentations/state/selection-controller.js",
                    "apps/presentations/state/history-controller.js",
                    "apps/presentations/ui/inspector-controller.js",
                    "apps/presentations/ui/thumbnails-controller.js",
                    "apps/presentations/ui/presenter-notes-controller.js",
                    "apps/presentations/presentation/slideshow-controller.js",
                    "apps/presentations/io/pptx-write-adapter.js",
                    "apps/presentations/io/file-controller.js",
                    "apps/presentations/io/recovery-controller.js",
                    "apps/presentations/app.js",
                ],
            )
            page.click("#newBtn")
            page.locator("#templateGrid .template-option").first.click()
            page.wait_for_selector("#app:not(.hidden)")
            initial = page.locator("#slideCanvas .obj").count()
            page.click('[data-tab="insert"]')
            page.click("#insertTextBtn")
            inserted = page.locator("#slideCanvas .obj").count()
            check(not page.locator("#undoBtn").is_disabled(), "Undo stayed disabled after inserting text")
            page.click("#undoBtn")
            undone = page.locator("#slideCanvas .obj").count()
            page.click("#redoBtn")
            redone = page.locator("#slideCanvas .obj").count()
            check(
                inserted == initial + 1 and undone == initial and redone == inserted,
                f"Presentation insert/undo/redo mismatch: {initial}, {inserted}, {undone}, {redone}",
            )
            report["checks"].append("presentation real insert/undo/redo runtime")

            # Pointer-driven move must participate in the same history contract.
            moved_obj = page.locator("#slideCanvas .obj").last
            box = moved_obj.bounding_box()
            check(box is not None, "Inserted presentation object has no pointer box")
            before_left = float(moved_obj.evaluate("el => parseFloat(el.style.left) || 0"))
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down()
            page.mouse.move(box["x"] + box["width"] / 2 + 70, box["y"] + box["height"] / 2 + 30, steps=4)
            page.mouse.up()
            after_left = float(page.locator("#slideCanvas .obj").last.evaluate("el => parseFloat(el.style.left) || 0"))
            check(after_left != before_left, f"Pointer move did not change object position: {before_left} -> {after_left}")
            check(not page.locator("#undoBtn").is_disabled(), "Undo stayed disabled after pointer move")
            page.click("#undoBtn")
            undo_left = float(page.locator("#slideCanvas .obj").last.evaluate("el => parseFloat(el.style.left) || 0"))
            check(abs(undo_left - before_left) < 1.0, f"Pointer move Undo failed: {before_left} -> {after_left} -> {undo_left}")
            page.click("#redoBtn")
            redo_left = float(page.locator("#slideCanvas .obj").last.evaluate("el => parseFloat(el.style.left) || 0"))
            check(abs(redo_left - after_left) < 1.0, f"Pointer move Redo failed: {after_left} -> {redo_left}")
            report["checks"].append("presentation pointer move undo/redo runtime")

            # Documents toolbar contract.
            page.set_content(text("apps/documents/index.html"))
            check(page.locator("#alignmentSelect").count() == 1, "alignment selector missing")
            check(
                page.locator('[data-cmd="indent"]').count() == 1
                and page.locator('[data-cmd="outdent"]').count() == 1,
                "indent controls missing",
            )
            check(
                page.locator('[data-cmd="insertUnorderedList"]').inner_text() == "•≡",
                "bulleted list not compact",
            )
            check(
                page.locator("#rowBtn").inner_text() == "▦↧"
                and page.locator("#colBtn").inner_text() == "▦↦",
                "row/column symbols incorrect",
            )
            check(
                page.locator('label[for="imageInput"]').inner_text() == "Insert",
                "insert image affordance incorrect",
            )
            report["checks"].append("Documents compact toolbar contract")

            # Real local PDF.js rendering: rapid jumps through a longer document
            # must leave every visible page backed by a canvas rather than a gray
            # loading placeholder. Also force the fullscreen fallback and prove
            # that it performs the scheduled post-layout rerender.
            with tempfile.TemporaryDirectory(prefix="inkdos-stability-pdf-") as temp_name:
                pdf_path = Path(temp_name) / "long-rendering.pdf"
                make_long_pdf(pdf_path)
                page.set_content(shell_html("apps/pdf/index.html"))
                add_styles(
                    page,
                    [
                        "apps/pdf/styles.css",
                        "shared/office-shell.css",
                        "shared/ui/polish.css",
                        "apps/pdf/fullscreen-mobile.css",
                    ],
                )
                add_scripts(
                    page,
                    [
                        "shared/office-runtime.js",
                        "modules/module-registry.js",
                        "modules/module-loader.js",
                        "shared/file-router.js",
                        "shared/vendor/pdfjs/pdf.min.js",
                        "apps/pdf/text-selection-review.js",
                        "apps/pdf/flatten-export.js",
                        "apps/pdf/io/save-controller.js",
                        "apps/pdf/review/annotation-layer.js",
                        "apps/pdf/review/review-controller.js",
                        "apps/pdf/viewer/navigation-controller.js",
                        "apps/pdf/viewer/page-renderer.js",
                        "apps/pdf/viewer/fullscreen-controller.js",
                        "apps/pdf/app.js",
                    ],
                )
                worker = text("shared/vendor/pdfjs/pdf.worker.min.js")
                page.evaluate(
                    "code => { pdfjsLib.GlobalWorkerOptions.workerSrc = URL.createObjectURL(new Blob([code], {type:'text/javascript'})); }",
                    worker,
                )
                page.set_input_files("#fileInput", str(pdf_path))
                page.wait_for_function("() => window.InkDOSPdfDebug?.getState().pageCount === 20")
                page.wait_for_function("() => window.InkDOSPdfDebug.getState().renderedCanvases >= 1")
                for target in (5, 10, 15, 20, 1, 12, 3, 18):
                    page.evaluate("n => window.InkDOSPdfDebug.goToPage(n)", target)
                    page.wait_for_function(
                        "n => window.InkDOSPdfDebug.getState().page === n", arg=target
                    )
                    page.wait_for_timeout(120)
                    visible = page.evaluate(
                        """() => {
                            const stage=document.querySelector('#viewerStage').getBoundingClientRect();
                            return [...document.querySelectorAll('.pdf-page-shell')]
                              .filter(node => { const r=node.getBoundingClientRect(); return r.bottom>stage.top && r.top<stage.bottom; })
                              .map(node => ({page:node.dataset.page, canvas:!!node.querySelector('canvas'), loading:!!node.querySelector('.page-loading')}));
                        }"""
                    )
                    check(
                        visible and all(item["canvas"] and not item["loading"] for item in visible),
                        f"visible gray PDF placeholder after jump to {target}: {visible}",
                    )
                report["checks"].append("PDF.js 20-page rapid navigation without visible gray placeholders")

                # Universal content-focus fullscreen: hide InkDOS editing chrome,
                # avoid native fullscreen and adapt the current page to the viewport.
                page.set_viewport_size({"width": 390, "height": 844})
                page.locator("#fullscreenBtn").click()
                page.wait_for_function("() => document.body.classList.contains('pdf-fullscreen') && document.body.classList.contains('immersive')")
                page.wait_for_function("() => window.InkDOSPdfDebug.getState().renderedCanvases >= 1")
                page.wait_for_timeout(160)
                focused = page.evaluate(
                    """() => ({
                        command:getComputedStyle(document.querySelector('.commandbar')).display,
                        status:getComputedStyle(document.querySelector('.statusbar')).display,
                        title:getComputedStyle(document.querySelector('.titlebar')).display,
                        stage:document.querySelector('#viewerStage').getBoundingClientRect().height,
                        canvases:window.InkDOSPdfDebug.getState().renderedCanvases,
                        nativeFullscreen:!!document.fullscreenElement,
                        appPosition:getComputedStyle(document.querySelector('#viewerApp')).position,
                        appTop:document.querySelector('#viewerApp').getBoundingClientRect().top,
                        appLeft:document.querySelector('#viewerApp').getBoundingClientRect().left,
                        appWidth:document.querySelector('#viewerApp').getBoundingClientRect().width,
                        pageWidth:(() => {
                          const current=window.InkDOSPdfDebug.getState().page;
                          return document.querySelector(`#viewerStage .pdf-page-shell[data-page="${current}"]`)?.getBoundingClientRect().width || 0;
                        })(),
                        stageWidth:document.querySelector('#viewerStage').getBoundingClientRect().width,
                        pressed:document.querySelector('#fullscreenBtn').getAttribute('aria-pressed')
                    })"""
                )
                check(focused["command"] == "none" and focused["status"] == "none" and focused["title"] == "none", f"content-focus chrome remains: {focused}")
                check(focused["stage"] > 760, f"content-focus mode did not use viewport height: {focused}")
                check(focused["canvases"] >= 1, f"content-focus mode lost rendered PDF canvases: {focused}")
                check(not focused["nativeFullscreen"], f"content-focus mode unexpectedly invoked native fullscreen: {focused}")
                check(focused["appPosition"] == "fixed" and abs(focused["appTop"]) < 1 and abs(focused["appLeft"]) < 1 and focused["appWidth"] >= 389, f"content-focus viewer is not pinned to viewport: {focused}")
                check(focused["pageWidth"] >= focused["stageWidth"] * 0.85 and focused["pageWidth"] <= focused["stageWidth"], f"fullscreen page did not adapt to viewport width: {focused}")
                check(focused["pressed"] == "true", f"fullscreen button did not expose active state: {focused}")
                report["checks"].append("PDF fullscreen hides chrome and adapts current page to viewport")

                page.evaluate("() => window.InkDOSPdfDebug.exitFullscreen()")
                page.wait_for_function("() => !document.body.classList.contains('pdf-fullscreen') && !document.body.classList.contains('immersive')")
                page.wait_for_function("() => window.InkDOSPdfDebug.getState().renderedCanvases >= 1")
                restored = page.evaluate(
                    """() => ({
                        command:getComputedStyle(document.querySelector('.commandbar')).display,
                        canvases:window.InkDOSPdfDebug.getState().renderedCanvases,
                        pressed:document.querySelector('#fullscreenBtn').getAttribute('aria-pressed')
                    })"""
                )
                check(restored["command"] != "none" and restored["canvases"] >= 1 and restored["pressed"] == "false", f"content-focus exit did not restore chrome/PDF state: {restored}")
                report["checks"].append("PDF content-focus exit restores controls and PDF rendering")

            report["passed"] = True
            context.close()
        finally:
            browser.close()

    (OUT / f"stability_corrections_candidate_{requested_browser_name()}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise RuntimeError("Stability corrections browser validation failed")


if __name__ == "__main__":
    main()
