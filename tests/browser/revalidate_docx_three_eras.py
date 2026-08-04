"""Optional browser compatibility test for the three synthetic Word-era fixtures.

Requirements:
    pip install playwright beautifulsoup4
    A Chromium executable available as CHROMIUM_PATH or /usr/bin/chromium.

Run from the repository root:
    python3 tests/browser/revalidate_docx_three_eras.py
"""
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from browser_support import launch_browser
from zipfile import ZipFile
import json
import os

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "compatibility-fixtures" / "documents"
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")


def load_app(page):
    soup = BeautifulSoup((ROOT / "apps/documents/index.html").read_text(), "html.parser")
    for node in soup.find_all(["script", "link"]):
        node.decompose()
    page.set_content(str(soup), wait_until="domcontentloaded")
    for css in (ROOT / "apps/documents/styles.css", ROOT / "shared/office-shell.css"):
        page.add_style_tag(path=str(css))
    for js in (
        ROOT / "shared/office-runtime.js",
        ROOT / "shared/file-lifecycle.js",
        ROOT / "shared/formula-engine.js",
        ROOT / "shared/safe-dom.js",
        ROOT / "shared/vendor/pako_inflate.min.js",
        ROOT / "apps/documents/docx-parser.js",
        ROOT / "shared/vendor/jszip.min.js",
        ROOT / "apps/documents/docx-writer.js",
        ROOT / "shared/office-shell.js",
        ROOT / "apps/documents/app.js",
    ):
        page.add_script_tag(path=str(js))


def package_features(path):
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        document = archive.read("word/document.xml").decode("utf-8", "replace")
        return {
            "parts": len(names),
            "header": any(n.startswith("word/header") for n in names),
            "footer": any(n.startswith("word/footer") for n in names),
            "numbering": "word/numbering.xml" in names,
            "image": any(n.startswith("word/media/") for n in names),
            "table": "<w:tbl" in document,
            "content_control": "<w:sdt" in document,
            "tracked_insert": "<w:ins" in document,
            "landscape": 'w:orient="landscape"' in document,
            "page_break": 'w:type="page"' in document,
        }


def main():
    results = []
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        for filename in (
            "era1_office_97_2003_legacy.doc",
            "era2_office_2007_2013_baseline.docx",
            "era3_office_2016_365_modern.docx",
        ):
            page = browser.new_page(viewport={"width": 1400, "height": 1000}, accept_downloads=True)
            dialogs, errors = [], []
            page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
            page.on("pageerror", lambda error: errors.append(str(error)))
            load_app(page)
            page.set_input_files("#fileInput", str(FIX / filename))
            if filename.endswith(".doc"):
                page.wait_for_timeout(300)
                results.append({"file": filename, "rejected": bool(dialogs), "message": dialogs[0] if dialogs else "", "errors": errors})
                page.close()
                continue
            page.wait_for_function("document.querySelector('#statusText').textContent.includes('opened')", timeout=30000)
            original = package_features(FIX / filename)
            page.locator(".page-content").last.evaluate("e=>{const p=document.createElement('p');p.textContent='DOCX-ROUNDTRIP-REGRESSION-MARKER';e.appendChild(p);e.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText'}));}")
            page.click("#saveBtn")
            page.wait_for_selector("#saveCopyDownload", timeout=30000)
            with page.expect_download(timeout=30000) as download_info:
                page.click("#saveCopyDownload")
            saved = OUT / (filename + ".saved.docx")
            download_info.value.save_as(str(saved))
            page.set_input_files("#fileInput", str(saved))
            page.wait_for_function("document.querySelector('#statusText').textContent.includes('reopened successfully')", timeout=30000)
            if "DOCX-ROUNDTRIP-REGRESSION-MARKER" not in page.locator("#pagesHost").inner_text():
                raise RuntimeError(f"Edited DOCX marker was not retained for {filename}")
            exported = package_features(saved)
            results.append({
                "file": filename,
                "pages": page.locator(".page").count(),
                "page_sizes": page.eval_on_selector_all(".page", "els=>els.map(e=>[parseFloat(e.style.width),parseFloat(e.style.height)])"),
                "images": page.locator(".page-content img").count(),
                "tables": page.locator(".page-content table").count(),
                "original": original,
                "exported": exported,
                "errors": errors,
            })
            page.close()
        browser.close()
    (OUT / "docx_three_eras.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
