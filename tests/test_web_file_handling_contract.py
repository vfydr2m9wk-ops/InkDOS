#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "documents": {"doc", "docx", "rtf"},
    "spreadsheets": {"xls", "xlsx", "csv", "tsv"},
    "presentations": {"ppt", "pptx"},
    "pdf": {"pdf"},
    "epub": {"epub"},
    "txt": {"txt", "xml", "md", "markdown", "json", "jsonl", "ndjson", "yaml", "yml", "log", "ini", "cfg", "conf", "toml", "properties"},
}


def handler_extensions(manifest: dict) -> set[str]:
    handlers = manifest.get("file_handlers")
    if not isinstance(handlers, list) or len(handlers) != 1:
        raise AssertionError(f"Expected exactly one file handler, got {handlers!r}")
    handler = handlers[0]
    if handler.get("action") != "./index.html":
        raise AssertionError(f"File handler action must stay app-local: {handler!r}")
    accept = handler.get("accept")
    if not isinstance(accept, dict) or not accept:
        raise AssertionError(f"File handler accept map missing: {handler!r}")
    out: set[str] = set()
    for mime, extensions in accept.items():
        if "/" not in mime or not isinstance(extensions, list) or not extensions:
            raise AssertionError(f"Invalid file handler accept entry: {mime!r} {extensions!r}")
        for extension in extensions:
            if not isinstance(extension, str) or not extension.startswith("."):
                raise AssertionError(f"Invalid handler extension: {extension!r}")
            out.add(extension[1:].lower())
    return out


def static_picker_extensions(app: str) -> set[str]:
    html = (ROOT / "apps" / app / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<input id="fileInput"[^>]*accept="([^"]+)"', html)
    if not match:
        raise AssertionError(f"{app}: canonical fileInput accept missing")
    return {token.strip()[1:].lower() for token in match.group(1).split(",") if token.strip().startswith(".")}


def main() -> None:
    desktop = json.loads((ROOT / "desktop" / "workspaces.json").read_text(encoding="utf-8"))
    tauri = json.loads((ROOT / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    associations = {
        item["name"]: {str(ext).lower().lstrip(".") for ext in item["ext"]}
        for item in tauri["bundle"]["fileAssociations"]
    }

    runtime_reference = None
    for app, expected in EXPECTED.items():
        root = ROOT / "apps" / app
        manifest = json.loads((root / "manifest.webmanifest").read_text(encoding="utf-8"))
        handled = handler_extensions(manifest)
        if handled != expected:
            raise AssertionError(f"{app}: manifest formats mismatch: {sorted(handled)} != {sorted(expected)}")

        desktop_extensions = {str(ext).lower().lstrip(".") for ext in desktop[app]["extensions"]}
        if desktop_extensions != expected:
            raise AssertionError(f"{app}: desktop workspace formats mismatch: {sorted(desktop_extensions)} != {sorted(expected)}")
        if associations.get(app) != expected:
            raise AssertionError(f"{app}: Tauri associations mismatch: {sorted(associations.get(app, set()))} != {sorted(expected)}")

        if app == "txt":
            policy = (root / "txt-policy.js").read_text(encoding="utf-8")
            declared = set(re.findall(r"'\.([a-z0-9]+)'", policy.split("const SUPPORTED=", 1)[1].split("]);", 1)[0]))
            if declared != expected:
                raise AssertionError(f"txt: policy formats mismatch: {sorted(declared)} != {sorted(expected)}")
        else:
            picker = static_picker_extensions(app)
            if picker != expected:
                raise AssertionError(f"{app}: picker formats mismatch: {sorted(picker)} != {sorted(expected)}")

        index = (root / "index.html").read_text(encoding="utf-8")
        if 'src="runtime/platform/file-launch.js"' not in index:
            raise AssertionError(f"{app}: file launch runtime not wired")

        launch_runtime = (root / "runtime" / "platform" / "file-launch.js").read_text(encoding="utf-8")
        for marker in ("launchQueue", "setConsumer", "handle.getFile", "DataTransfer", "compatibleInput", "input.dispatchEvent(new Event('change'"):
            if marker not in launch_runtime:
                raise AssertionError(f"{app}: launched-file bridge missing {marker!r}")
        if runtime_reference is None:
            runtime_reference = launch_runtime
        elif launch_runtime != runtime_reference:
            raise AssertionError(f"{app}: copied launched-file bridge drifted from the validated implementation")

    # Converted legacy imports must keep their existing safe-copy semantics.
    documents = (ROOT / "apps" / "documents" / "io" / "file-open-controller.js").read_text(encoding="utf-8")
    doc_save = (ROOT / "apps" / "documents" / "io" / "save-controller.js").read_text(encoding="utf-8")
    if "Save editable DOCX copy" not in documents or "session.kind==='doc'" not in doc_save:
        raise AssertionError("Documents legacy DOC conversion guard missing")
    if "legacyOutputName(file.name)" not in documents:
        raise AssertionError("RTF import must target a DOCX copy name")

    sheets_delivery = (ROOT / "apps" / "spreadsheets" / "io" / "file-delivery.js").read_text(encoding="utf-8")
    if "sourceKind==='csv'?'.csv':sourceKind==='tsv'?'.tsv':'.xlsx'" not in sheets_delivery:
        raise AssertionError("Spreadsheets must preserve CSV/TSV and convert legacy spreadsheet saves to XLSX")

    pres_save = (ROOT / "apps" / "presentations" / "io" / "save-controller.js").read_text(encoding="utf-8")
    if "legacy-ppt-to-editable-pptx" not in pres_save or "n.replace(/\.ppt$/i,'.pptx')" not in pres_save:
        raise AssertionError("Presentations legacy PPT conversion guard missing")

    txt_delivery = (ROOT / "apps" / "txt" / "runtime" / "services" / "file-delivery.js").read_text(encoding="utf-8")
    if "P&&typeof P.isSupportedName==='function'&&P.isSupportedName(n)?n" not in txt_delivery:
        raise AssertionError("Plain Text save must preserve every approved source extension")

    service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    for app in EXPECTED:
        for rel in (f"./apps/{app}/manifest.webmanifest", f"./apps/{app}/runtime/platform/file-launch.js"):
            if f'"{rel}"' not in service_worker:
                raise AssertionError(f"Offline shell missing {rel}")

    print("InkDOS 2.6 web/native file handling contract: OK")


if __name__ == "__main__":
    main()
