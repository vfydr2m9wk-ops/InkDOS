#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "apps" / "pdf"

DYNAMIC_PDF_ASSETS = (
    "features/reader/reader-runtime.js",
    "ui/reader-tools.js",
    "vendor/jszip.min.js",
    "vendor/pdf-lib/pdf-lib.min.js",
    "engine/page-tools-engine.js",
    "ui/page-tools.js",
    "runtime/commands/command-registry.js",
    "ui/command-bindings.js",
    "ui/toolbar-rail.js",
    "ui/mode-bindings.js",
    "features/page-tools/page-tools-runtime.js",
    "features/page-tools/actions/move-page.js",
    "features/page-tools/actions/rotate-page.js",
    "features/page-tools/actions/delete-page.js",
    "features/page-tools/actions/extract-page.js",
    "features/page-tools/actions/split-pdf.js",
    "features/page-tools/actions/merge-pdfs.js",
)

def main() -> None:
    app = (PDF / "app.js").read_text(encoding="utf-8")
    service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    root_index = (ROOT / "index.html").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "pdf-stability-regression.yml").read_text(encoding="utf-8")

    for relative in DYNAMIC_PDF_ASSETS:
        assert relative in app, f"PDF bootstrap no longer references expected dynamic asset: {relative}"
        precache_entry = f'"./apps/pdf/{relative}"'
        assert precache_entry in service_worker, f"PDF dynamic asset missing from offline APP_SHELL: {relative}"

    assert '"./apps/pdf/"' in service_worker, "Canonical PDF directory navigation is not handled offline"
    assert '"./apps/pdf/index.html"' in service_worker
    assert "navigator.serviceWorker.register('./service-worker.js'" in root_index
    assert "service-worker.js" in workflow
    assert "test_pdf_stability_offline.py" in workflow
    assert "test_pdf_p2_page_tools.cjs" in workflow

    print("PDF offline/static shell contract passed.")

if __name__ == "__main__":
    main()
