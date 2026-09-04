"""Validate shared package, XML, filename, and resource-safety guards."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from playwright.sync_api import sync_playwright
from browser_support import launch_browser, requested_browser_name

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests" / "browser" / "results"
OUT.mkdir(parents=True, exist_ok=True)
CHROMIUM = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")


def make_zip(name: str, payload: bytes) -> bytes:
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as package:
        package.writestr(name, payload)
    return stream.getvalue()


def tamper_local_offset(data: bytes) -> bytes:
    modified = bytearray(data)
    signature = b"PK\x01\x02"
    offset = modified.find(signature)
    if offset < 0:
        raise RuntimeError("Central-directory signature was not found")
    modified[offset + 42 : offset + 46] = (len(modified) + 100).to_bytes(4, "little")
    return bytes(modified)


def validate(page, data: bytes, label: str, limits=None):
    return page.evaluate(
        """({bytes,label,limits}) => {
          try {
            const value=InkDOSRuntime.validateZipPackage(new Uint8Array(bytes),label,limits);
            return {ok:true,value};
          } catch(error) {
            return {ok:false,message:error.message};
          }
        }""",
        {"bytes": list(data), "label": label, "limits": limits},
    )


def main():
    safe = make_zip("word/document.xml", b"<document>safe</document>")
    unsafe_path = make_zip("../evil.xml", b"bad")
    control_path = make_zip("word/bad\x01.xml", b"bad")
    malformed_offset = tamper_local_offset(safe)

    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content("<!doctype html><html><body></body></html>")
        page.add_script_tag(path=str(ROOT / "shared/office-runtime.js"))

        cases = {
            "safe": validate(page, safe, "Safe package"),
            "empty": validate(page, b"", "Empty package"),
            "unsafe_path": validate(page, unsafe_path, "Unsafe package"),
            "control_path": validate(page, control_path, "Control package"),
            "malformed_local_offset": validate(page, malformed_offset, "Malformed package"),
            "entry_limit": validate(page, safe, "Entry-limited package", {"maxEntries": 0}),
            "entry_size_limit": validate(page, safe, "Size-limited package", {"maxEntryUncompressedBytes": 1}),
        }
        invalid_xml = page.evaluate(
            """() => {try{InkDOSRuntime.parseXml('<root>','test XML');return {ok:true}}catch(error){return {ok:false,message:error.message}}}"""
        )
        filename = page.evaluate("InkDOSRuntime.sanitizeFileName('  bad<>:\"/\\\\|?* name.docx  ')")
        browser.close()

    expected_failures = [
        "empty",
        "unsafe_path",
        "control_path",
        "malformed_local_offset",
        "entry_limit",
        "entry_size_limit",
    ]
    problems = []
    if not cases["safe"]["ok"] or cases["safe"]["value"]["entries"] != 1:
        problems.append(f"Safe package rejected: {cases['safe']}")
    for key in expected_failures:
        if cases[key]["ok"]:
            problems.append(f"Unsafe case was accepted: {key}")
    if invalid_xml["ok"]:
        problems.append("Malformed XML was accepted")
    if any(character in filename for character in '<>:"/\\|?*'):
        problems.append(f"Filename was not sanitized: {filename!r}")
    if errors:
        problems.extend(errors)
    if problems:
        raise RuntimeError("Office runtime guard validation failed: " + " | ".join(problems))

    result = {"cases": cases, "invalid_xml": invalid_xml, "sanitized_filename": filename, "page_errors": errors}
    (OUT / "office_runtime_guards.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
