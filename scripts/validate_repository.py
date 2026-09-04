#!/usr/bin/env python3
"""Static repository checks for InkDOS."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ALLOW_VENDOR_BOOTSTRAP = '--allow-vendor-bootstrap' in sys.argv
BOOTSTRAP_VENDOR_PATHS = {
    'shared/vendor/pdfjs/pdf.min.js',
    'shared/vendor/pdfjs/pdf.worker.min.js',
    'shared/vendor/pdfjs/LICENSE-PDFJS.txt',
}
EXCLUDED_PARTS = {".git", "node_modules", "__pycache__", "test-results"}
EXCLUDED_PREFIXES = {("tests", "browser", "results")}
NEUTRAL_BRAND_PATTERN = re.compile("xe" + "os", re.IGNORECASE)
ABSOLUTE_HOST_PATTERN = re.compile("file:///var/mobile/" + "Containers|/var/mobile/" + "Containers")
DEVELOPMENT_URL_PATTERN = re.compile(r"(?:https?://)?(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?", re.I)
CSS_URL_PATTERN = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)
SOURCE_MAP_PATTERN = re.compile(r"[#@]\s*sourceMappingURL\s*=\s*([^\s*]+)")
SERVICE_WORKER_SHELL_PATTERN = re.compile(r"const\s+APP_SHELL\s*=\s*\[(.*?)\]\s*;", re.S)
STRING_LITERAL_PATTERN = re.compile(r"['\"]([^'\"]+)['\"]")


class HTMLInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.refs: list[tuple[str, str, str]] = []
        self.manifests: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        for key in ("src", "href"):
            value = values.get(key)
            if value:
                self.refs.append((tag, key, value))
        rel = (values.get("rel") or "").lower().split()
        if tag == "link" and "manifest" in rel and values.get("href"):
            self.manifests.append(values["href"] or "")
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"] or "")


def is_excluded(path: Path) -> bool:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return True
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return True
    return any(rel.parts[: len(prefix)] == prefix for prefix in EXCLUDED_PREFIXES)


def iter_files(pattern: str):
    for path in ROOT.rglob(pattern):
        if path.is_file() and not is_excluded(path):
            yield path


def is_external(ref: str) -> bool:
    parsed = urlparse(ref)
    return bool(parsed.scheme in {"http", "https", "mailto", "tel", "data", "blob", "javascript"} or ref.startswith("#"))


def resolve_local_reference(source: Path, ref: str, errors: list[str], label: str) -> Path | None:
    clean = ref.split("#", 1)[0].split("?", 1)[0]
    if not clean or is_external(ref):
        return None
    if clean.startswith("/"):
        errors.append(f"Root-absolute {label}: {source.relative_to(ROOT)} -> {ref}")
        return None
    target = (source.parent / clean).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"Reference escapes repository: {source.relative_to(ROOT)} -> {ref}")
        return None
    if not target.exists():
        try:
            target_relative = target.relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            target_relative = ''
        if ALLOW_VENDOR_BOOTSTRAP and target_relative in BOOTSTRAP_VENDOR_PATHS and (ROOT / 'VENDOR_SOURCES.json').is_file():
            return target
        errors.append(f"Missing local {label}: {source.relative_to(ROOT)} -> {ref}")
        return None
    return target


def load_json(path: Path, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSON: {path.relative_to(ROOT)}: {exc}")
        return None


def validate_web_manifest(manifest: object, errors: list[str]) -> None:
    path = ROOT / "manifest.webmanifest"
    if not isinstance(manifest, dict):
        return
    for field in ("name", "short_name", "start_url", "scope", "display", "icons"):
        if not manifest.get(field):
            errors.append(f"Web manifest field is missing or empty: {field}")
    if manifest.get("display") not in {"standalone", "minimal-ui", "fullscreen", "browser"}:
        errors.append("Web manifest has an invalid display mode")
    for ref in (manifest.get("start_url"), manifest.get("scope")):
        if isinstance(ref, str):
            resolve_local_reference(path, ref, errors, "web manifest reference")
    icons = manifest.get("icons", [])
    if not isinstance(icons, list) or not icons:
        errors.append("Web manifest must contain at least one icon")
    else:
        for icon in icons:
            if not isinstance(icon, dict) or not icon.get("src"):
                errors.append("Web manifest contains an icon without src")
                continue
            resolve_local_reference(path, str(icon["src"]), errors, "web manifest icon")
    for shortcut in manifest.get("shortcuts", []):
        if isinstance(shortcut, dict) and shortcut.get("url"):
            resolve_local_reference(path, str(shortcut["url"]), errors, "web manifest shortcut")


def validate_service_worker(errors: list[str], version: str | None) -> None:
    path = ROOT / "service-worker.js"
    if not path.is_file():
        errors.append("Required file missing: service-worker.js")
        return
    text = path.read_text(encoding="utf-8")
    match = SERVICE_WORKER_SHELL_PATTERN.search(text)
    if not match:
        errors.append("service-worker.js does not expose a static APP_SHELL list")
        return
    shell = STRING_LITERAL_PATTERN.findall(match.group(1))
    if not shell:
        errors.append("service-worker.js APP_SHELL is empty")
    for ref in shell:
        resolve_local_reference(path, ref, errors, "service-worker cache entry")
    required_entries = {
        "./index.html",
        "./manifest.webmanifest",
        "./shared/office-runtime.js",
        "./apps/documents/index.html",
        "./apps/spreadsheets/index.html",
        "./apps/presentations/index.html",
    }
    missing = sorted(required_entries.difference(shell))
    if missing:
        errors.append("Service-worker app shell is missing required entries: " + ", ".join(missing))
    if version and f"inkdos-shell-v{version}" not in text:
        errors.append("Service-worker cache version does not match VERSION.json")
    if re.search(r"\b(?:importScripts|fetch)\s*\(\s*['\"]https?://", text):
        errors.append("Service worker contains an automatic remote dependency")


def main() -> int:
    errors: list[str] = []

    json_docs: dict[Path, object] = {}
    for path in iter_files("*.json"):
        value = load_json(path, errors)
        if value is not None:
            json_docs[path] = value
    web_manifest_path = ROOT / "manifest.webmanifest"
    web_manifest = load_json(web_manifest_path, errors) if web_manifest_path.is_file() else None
    if web_manifest is None and not web_manifest_path.is_file():
        errors.append("Required file missing: manifest.webmanifest")

    html_inspectors: dict[Path, HTMLInspector] = {}
    for path in iter_files("*.html"):
        parser = HTMLInspector()
        try:
            parser.feed(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Invalid HTML parse: {path.relative_to(ROOT)}: {exc}")
            continue
        html_inspectors[path] = parser

        duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
        if duplicates:
            errors.append(f"Duplicate HTML IDs in {path.relative_to(ROOT)}: {', '.join(duplicates)}")

        for _tag, _attribute, ref in parser.refs:
            resolve_local_reference(path, ref, errors, "reference")

    primary_pages = [
        ROOT / "index.html",
        ROOT / "apps/documents/index.html",
        ROOT / "apps/spreadsheets/index.html",
        ROOT / "apps/presentations/index.html",
    ]
    for path in primary_pages:
        parser = html_inspectors.get(path)
        if not parser:
            continue
        if not parser.manifests:
            errors.append(f"Primary page does not link the web manifest: {path.relative_to(ROOT)}")
        if not any("register-service-worker.js" in script for script in parser.scripts):
            errors.append(f"Primary page does not load guarded service-worker registration: {path.relative_to(ROOT)}")

    for path in iter_files("*.css"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for _quote, ref in CSS_URL_PATTERN.findall(text):
            if ref.strip().startswith(("data:", "blob:", "#", "var(")):
                continue
            resolve_local_reference(path, ref.strip(), errors, "CSS asset")

    for pattern in ("*.js", "*.css"):
        for path in iter_files(pattern):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for ref in SOURCE_MAP_PATTERN.findall(text):
                resolve_local_reference(path, ref.strip(), errors, "source map")

    text_extensions = {".html", ".css", ".js", ".md", ".json", ".webmanifest", ".yml", ".yaml", ".txt", ".py"}
    runtime_extensions = {".html", ".css", ".js"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or is_excluded(path) or path.suffix.lower() not in text_extensions:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if NEUTRAL_BRAND_PATTERN.search(text):
            errors.append(f"Legacy product reference found: {path.relative_to(ROOT)}")
        if ABSOLUTE_HOST_PATTERN.search(text):
            errors.append(f"Device-specific path found: {path.relative_to(ROOT)}")
        if path.suffix.lower() in runtime_extensions and "vendor" not in path.parts and DEVELOPMENT_URL_PATTERN.search(text):
            errors.append(f"Development URL found in runtime file: {path.relative_to(ROOT)}")

    case_map: dict[str, list[Path]] = {}
    for path in ROOT.rglob("*"):
        if path.is_file() and not is_excluded(path):
            key = str(path.relative_to(ROOT)).casefold()
            case_map.setdefault(key, []).append(path.relative_to(ROOT))
    for matches in case_map.values():
        if len(matches) > 1:
            errors.append("Case-insensitive filename conflict: " + ", ".join(map(str, matches)))

    node = shutil.which("node")
    if node:
        for path in iter_files("*.js"):
            if "vendor" in path.parts:
                continue
            result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
            if result.returncode:
                detail = (result.stderr or result.stdout).strip().splitlines()[-1]
                errors.append(f"Invalid JavaScript syntax: {path.relative_to(ROOT)}: {detail}")
    else:
        print("Warning: Node.js is unavailable; JavaScript syntax checks were not performed.")

    required = [
        ROOT / "index.html",
        ROOT / "LICENSE",
        ROOT / "README.md",
        ROOT / "app-manifest.json",
        ROOT / "manifest.webmanifest",
        ROOT / "service-worker.js",
        ROOT / "shared/register-service-worker.js",
        ROOT / "shared/vendor/jszip.min.js",
        ROOT / "shared/vendor/pako_inflate.min.js",
        ROOT / "shared/vendor/LICENSE-JSZIP.txt",
        ROOT / "shared/vendor/LICENSE-PAKO.txt",
        ROOT / "VERSION.json",
        ROOT / "apps/documents/index.html",
        ROOT / "apps/spreadsheets/index.html",
        ROOT / "apps/presentations/index.html",
        ROOT / "tests/fixtures/minimal.docx",
        ROOT / "tests/fixtures/minimal.xlsx",
        ROOT / "tests/fixtures/minimal.pptx",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"Required file missing: {path.relative_to(ROOT)}")

    for workspace in ("documents", "spreadsheets", "presentations"):
        vendor_dir = ROOT / "apps" / workspace / "vendor"
        if vendor_dir.exists() and any(vendor_dir.iterdir()):
            errors.append(f"Workspace contains a duplicate vendor directory: {vendor_dir.relative_to(ROOT)}")

    manifest = json_docs.get(ROOT / "app-manifest.json")
    version = json_docs.get(ROOT / "VERSION.json")
    package = json_docs.get(ROOT / "package.json")
    release_manifest = json_docs.get(ROOT / "RELEASE_MANIFEST.json")
    expected_version = version.get("version") if isinstance(version, dict) else None
    if isinstance(manifest, dict) and expected_version:
        if manifest.get("version") != expected_version:
            errors.append("Version mismatch between app-manifest.json and VERSION.json")
        if not isinstance(package, dict) or package.get("version") != expected_version:
            errors.append("Version mismatch between package.json and VERSION.json")
        if not isinstance(release_manifest, dict) or release_manifest.get("version") != expected_version:
            errors.append("Version mismatch between RELEASE_MANIFEST.json and VERSION.json")
        for launcher in manifest.get("launchers", []):
            target = ROOT / launcher.get("entryPoint", "")
            if not target.is_file():
                errors.append(f"Manifest launcher is missing: {launcher.get('entryPoint')}")

    validate_web_manifest(web_manifest, errors)
    validate_service_worker(errors, str(expected_version) if expected_version else None)

    if errors:
        print("Repository validation failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    html_count = sum(1 for _ in iter_files("*.html"))
    json_count = sum(1 for _ in iter_files("*.json")) + (1 if web_manifest_path.is_file() else 0)
    print(f"Repository validation passed ({html_count} HTML files, {json_count} JSON/manifest files).")
    return 0


if __name__ == "__main__":
    if ALLOW_VENDOR_BOOTSTRAP:
        sys.argv.remove('--allow-vendor-bootstrap')
    sys.exit(main())
