#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = ("documents", "spreadsheets", "presentations", "pdf", "epub", "txt")
LOCALES = {
    "pt-BR": "Português",
    "es": "Español",
    "de": "Deutsch",
    "fr": "Français",
    "zh-CN": "中文（简体）",
    "ja": "日本語",
    "ru": "Русский",
}
RUNTIME = ROOT / "shared" / "localization" / "ui-localization.js"
LOCALE_DIR = ROOT / "shared" / "localization" / "locales"
CSS = ROOT / "shared" / "localization" / "localization.css"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: forbidden {needle!r}")


def main() -> None:
    if not RUNTIME.is_file():
        raise AssertionError("Missing isolated localization runtime: shared/localization/ui-localization.js")
    if not LOCALE_DIR.is_dir():
        raise AssertionError("Missing isolated locale directory: shared/localization/locales")
    if not CSS.is_file():
        raise AssertionError("Missing localization/settings overflow stylesheet")

    runtime = RUNTIME.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    # English must remain the raw/native path and must not have a package.
    if (LOCALE_DIR / "en.js").exists() or (LOCALE_DIR / "en-US.js").exists():
        raise AssertionError("English must not have a translation package")
    require(runtime, "DEFAULT_LANGUAGE='en'", "Native English path")
    require(runtime, "ALLOWED_ATTRIBUTES", "Presentation-only attribute allowlist")
    for attr in ("title", "aria-label", "placeholder"):
        require(runtime, repr(attr), "Translation attribute allowlist")
    for forbidden_attr in (
        "'id'", '"id"', "'data-action'", '"data-action"', "'data-cmd'", '"data-cmd"',
        "'value'", '"value"', "'name'", '"name"', "'href'", '"href"',
    ):
        forbid(runtime, forbidden_attr, "Localization runtime must not mutate functional attributes")
    for network_api in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon"):
        forbid(runtime, network_api, "Localization must remain local-first/offline")

    expected_files = {f"{code}.js" for code in LOCALES}
    actual_files = {p.name for p in LOCALE_DIR.glob("*.js")}
    if actual_files != expected_files:
        raise AssertionError(f"Locale packages mismatch: expected {sorted(expected_files)}, got {sorted(actual_files)}")

    for code, display in LOCALES.items():
        package = (LOCALE_DIR / f"{code}.js").read_text(encoding="utf-8")
        require(package, code, f"Locale identity {code}")
        require(package, display, f"Locale display name {code}")
        for forbidden in ("querySelector", "setAttribute", "textContent", "innerHTML", "localStorage", "fetch("):
            forbid(package, forbidden, f"Locale package {code} must contain data only")

    # Runtime-level probe: fallback to raw English and no English package load.
    probe = r'''
const fs=require('fs');
const vm=require('vm');
const path=process.argv[1];
global.document=undefined;
global.window=global;
vm.runInThisContext(fs.readFileSync(path,'utf8'),{filename:path});
const api=globalThis.InkDOSLocalization;
if(!api)throw new Error('InkDOSLocalization API missing');
const out={
  nativePath:api.packagePath('en'),
  portuguesePath:api.packagePath('pt-BR'),
  invalid:api.normalizeLanguage('xx'),
  fallback:api.translateValue({'known':'Traduzido'},'missing','Original English'),
  translated:api.translateValue({'known':'Traduzido'},'known','Original English'),
  languages:api.languages.map(item=>[item.code,item.label])
};
process.stdout.write(JSON.stringify(out));
'''
    completed = subprocess.run(
        ["node", "-e", probe, str(RUNTIME)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)
    if result["nativePath"] is not None:
        raise AssertionError("English path must not load a language package")
    if result["portuguesePath"] != "pt-BR.js":
        raise AssertionError(f"Unexpected pt-BR package path: {result['portuguesePath']!r}")
    if result["invalid"] != "en":
        raise AssertionError("Unknown languages must fall back to raw English")
    if result["fallback"] != "Original English":
        raise AssertionError("Missing translations must fall back to raw English text")
    if result["translated"] != "Traduzido":
        raise AssertionError("Known translation did not resolve")
    if result["languages"] != [["en", "English"], *[[code, label] for code, label in LOCALES.items()]]:
        raise AssertionError(f"Language menu mismatch: {result['languages']!r}")

    # Each workspace owns its preference and exposes the same compact settings order.
    for app in APPS:
        state = ROOT / "apps" / app / "state" / "language.js"
        if not state.is_file():
            raise AssertionError(f"Missing app-local language state: {state.relative_to(ROOT)}")
        state_text = state.read_text(encoding="utf-8")
        require(state_text, f"inkdos2:{app}:language", f"App-local language persistence: {app}")
        forbid(state_text, "inkdos2:language", f"Language state must not be suite-global: {app}")

        entry = ROOT / "apps" / app / ("page.template.html" if app == "txt" else "index.html")
        html = entry.read_text(encoding="utf-8")
        require(html, "../../shared/localization/ui-localization.js", f"Localization runtime integration: {app}")
        require(html, "../../shared/localization/localization.css", f"Localization CSS integration: {app}")
        require(html, "state/language.js", f"App-local language state integration: {app}")

        markers = [
            'data-settings-item="appearance"',
            'data-settings-item="interface"',
            'data-settings-item="language"',
            'data-settings-item="help"',
        ]
        positions = [html.find(marker) for marker in markers]
        if any(pos < 0 for pos in positions):
            raise AssertionError(f"Missing compact settings item(s) in {entry.relative_to(ROOT)}: {positions}")
        if positions != sorted(positions):
            raise AssertionError(f"Settings order must be Appearance, Interface, Language, Help: {entry.relative_to(ROOT)}")

    # Overflow safeguards for long Latin/Cyrillic/CJK labels.
    for needle in ("overflow-wrap", "max-inline-size", "text-overflow"):
        require(css, needle, "Localization overflow guard")
    require(css, "[data-settings-item]", "Compact settings CSS")

    # The service worker must cache all local localization assets; no network translation service.
    service_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    require(service_worker, '"./shared/localization/ui-localization.js"', "Offline localization runtime")
    require(service_worker, '"./shared/localization/localization.css"', "Offline localization CSS")
    for code in LOCALES:
        require(service_worker, f'"./shared/localization/locales/{code}.js"', f"Offline locale package {code}")

    print("InkDOS 2.4 localization/settings contract: OK")


if __name__ == "__main__":
    main()
