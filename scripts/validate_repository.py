#!/usr/bin/env python3
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ("documents", "spreadsheets", "presentations", "txt", "epub", "pdf")


def main() -> None:
    required = (
        "index.html",
        "VERSION.json",
        "manifest.webmanifest",
        "service-worker.js",
        "README.md",
    )
    for rel in required:
        if not (ROOT / rel).is_file():
            raise SystemExit(f"Required file missing: {rel}")

    version_data = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
    version = version_data.get("version")
    development_version = version_data.get("developmentVersion")
    if not isinstance(version, str) or re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        raise SystemExit("Invalid release version")
    if development_version is not None and (
        not isinstance(development_version, str)
        or re.fullmatch(r"\d+\.\d+", development_version) is None
    ):
        raise SystemExit("Invalid developmentVersion")

    dirs = sorted(path.name for path in (ROOT / "apps").iterdir() if path.is_dir())
    if dirs != sorted(ACTIVE):
        raise SystemExit(f"Unexpected app roots: {dirs}")

    home = (ROOT / "index.html").read_text(encoding="utf-8")
    for app in ACTIVE:
        if f"./apps/{app}/index.html?v={version}&amp;suite=1" not in home:
            raise SystemExit(f"Versioned suite Home route missing: {app}")
        index = ROOT / "apps" / app / "index.html"
        text = index.read_text(encoding="utf-8")
        if "../../index.html" not in text or 'aria-label="Home"' not in text:
            raise SystemExit(f"Optional Home anchor missing: {app}")

    if "PDF Workspace" not in home or "Coming soon" in home:
        raise SystemExit("PDF route must be active")
    if (ROOT / "apps/pdf/assets/pdf.svg").read_bytes() != (ROOT / "assets/icons/pdf.svg").read_bytes():
        raise SystemExit("PDF app icon must match canonical Home icon")

    pdf_frame = (ROOT / "apps/pdf/runtime/frame/app-frame.css").read_text(encoding="utf-8")
    for marker in (
        ".document-title{position:absolute;left:50%",
        ".title-text{height:100%",
        "border:1px solid var(--line)",
        ".pdf-icon{width:30px",
    ):
        if marker not in pdf_frame:
            raise SystemExit("PDF frame title alignment missing: " + marker)

    if (
        "inkdos2:appearance" not in home
        or 'id="appearanceButton"' not in home
        or 'id="appearanceMenu"' not in home
    ):
        raise SystemExit("Home appearance control missing")

    home_css = (ROOT / "assets/home.css").read_text(encoding="utf-8")
    if 'html[data-theme="dark"]' not in home_css:
        raise SystemExit("Home dark appearance missing")

    local_keys = {
        "documents": "inkdos2:documents:appearance",
        "spreadsheets": "inkdos2:spreadsheets:appearance",
        "presentations": "inkdos2:presentations:appearance",
        "txt": "inkdos2:txt:appearance",
        "epub": "inkdos2:epub:appearance",
        "pdf": "inkdos2:pdf:p1:appearance",
    }
    for app, local_key in local_keys.items():
        appearance = (ROOT / "apps" / app / "state" / "appearance.js").read_text(encoding="utf-8")
        if local_key not in appearance:
            raise SystemExit(f"App-local appearance key missing: {app}")
        if "inkdos2:appearance" not in appearance or "'storage'" not in appearance:
            raise SystemExit(f"Horizontal appearance bridge missing: {app}")

    starts = {
        "documents": ("startNew", "startOpen"),
        "spreadsheets": ("startNew", "startOpen"),
        "presentations": ("startNew", "startOpen"),
        "txt": ("startNew", "startOpen"),
        "epub": ("openStartBtn",),
        "pdf": ("openStartBtn",),
    }
    for app, ids in starts.items():
        text = (ROOT / "apps" / app / "index.html").read_text(encoding="utf-8")
        if "start-card" not in text:
            raise SystemExit(f"Standard start card missing: {app}")
        for ident in ids:
            if f'id="{ident}"' not in text:
                raise SystemExit(f"Start action {ident} missing: {app}")

    presentation = (ROOT / "apps/presentations/index.html").read_text(encoding="utf-8")
    for marker in ("presentationStartGate", "showStart()", "waitForOpenCommit", "app.newPresentation()"):
        if marker not in presentation:
            raise SystemExit(f"Presentations startup gate missing: {marker}")
    if (
        "display:grid!important" not in presentation
        or ".start-state[hidden]{display:none!important}" not in presentation
    ):
        raise SystemExit("Presentations startup gate visibility contract missing")

    pdf = (ROOT / "apps/pdf/index.html").read_text(encoding="utf-8")
    for marker in ("pdfStartGate", "new MutationObserver(syncStart)", "syncStart()"):
        if marker not in pdf:
            raise SystemExit("PDF start gate missing: " + marker)
    if list((ROOT / "apps/pdf").rglob("*.pdf")) or (ROOT / "apps/pdf/tests").exists():
        raise SystemExit("PDF distribution contains internal fixtures")

    service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    if development_version:
        cache_pattern = rf"const CACHE_NAME=['\"]inkdos-v{re.escape(development_version)}-dev-[^'\"]+['\"]"
        cache_label = f"{development_version} development"
    else:
        cache_pattern = rf"const CACHE_NAME=['\"]inkdos-v{re.escape(version)}-[^'\"]+['\"]"
        cache_label = version
    if not re.search(cache_pattern, service_worker):
        raise SystemExit(f"{cache_label} offline cache rotation missing")

    for marker in (
        "suite-shell.js",
        "file-router.js",
        "recent-files.js",
        "module-loader.js",
        "shared/app-shell.js",
    ):
        if marker in home:
            raise SystemExit(f"Legacy Home runtime reference: {marker}")

    print("Repository runtime structure validated.")


if __name__ == "__main__":
    main()
