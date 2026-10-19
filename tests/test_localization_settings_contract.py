#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
SETTINGS = ROOT / "shared" / "localization" / "settings-strip.js"
LOCALE_DIR = ROOT / "shared" / "localization" / "locales"
CSS = ROOT / "shared" / "localization" / "localization.css"
DENSITY = ROOT / "shared" / "ui-density.js"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        raise AssertionError(f"{label}: forbidden {needle!r}")


def main() -> None:
    for path, label in [
        (RUNTIME, "isolated localization runtime"),
        (SETTINGS, "isolated settings strip"),
        (CSS, "localization/settings stylesheet"),
        (DENSITY, "density bootstrap"),
    ]:
        if not path.is_file():
            raise AssertionError(f"Missing {label}: {path.relative_to(ROOT)}")
    if not LOCALE_DIR.is_dir():
        raise AssertionError("Missing isolated locale directory")

    runtime = RUNTIME.read_text(encoding="utf-8")
    settings = SETTINGS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    density = DENSITY.read_text(encoding="utf-8")

    # English is the raw/native UI and never has a translation package.
    if (LOCALE_DIR / "en.js").exists() or (LOCALE_DIR / "en-US.js").exists():
        raise AssertionError("English must not have a translation package")
    require(runtime, "DEFAULT_LANGUAGE='en'", "Native English path")
    require(runtime, "ALLOWED_ATTRIBUTES", "Presentation-only attribute allowlist")
    for attr in ("title", "aria-label", "placeholder"):
        require(runtime, repr(attr), "Translation attribute allowlist")
    for forbidden_attr in (
        "'data-action'", '"data-action"', "'data-cmd'", '"data-cmd"',
        "'value'", '"value"', "'name'", '"name"', "'href'", '"href"',
    ):
        forbid(runtime, forbidden_attr, "Localization runtime must not mutate functional attributes")
    for network_api in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon"):
        forbid(runtime, network_api, "Localization must stay local-only")
    require(runtime, "purgePackages", "Single selected locale residency")
    require(runtime, "data-inkdos-locale-package", "Non-functional locale package lifecycle marker")
    forbid(runtime, "inkdosLocalePackage-", "Locale package lifecycle must not create functional IDs")

    expected_files = {f"{code}.js" for code in LOCALES}
    actual_files = {p.name for p in LOCALE_DIR.glob("*.js")}
    if actual_files != expected_files:
        raise AssertionError(f"Locale packages mismatch: expected {sorted(expected_files)}, got {sorted(actual_files)}")
    for code, display in LOCALES.items():
        package = (LOCALE_DIR / f"{code}.js").read_text(encoding="utf-8")
        require(package, code, f"Locale identity {code}")
        require(package, display, f"Locale display name {code}")
        require(package, "Loading…", f"Loading state translation {code}")
        for forbidden in ("querySelector", "setAttribute", "textContent", "innerHTML", "localStorage", "fetch("):
            forbid(package, forbidden, f"Locale package {code} must contain data only")

    # Pure runtime probe: fallback must be raw English and English has no package path.
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
        ["node", "-e", probe, str(RUNTIME)], cwd=ROOT, check=True, text=True, capture_output=True
    )
    result = json.loads(completed.stdout)
    expected_languages = [["en", "English"], *[[code, label] for code, label in LOCALES.items()]]
    assert result["nativePath"] is None, result
    assert result["portuguesePath"] == "pt-BR.js", result
    assert result["invalid"] == "en", result
    assert result["fallback"] == "Original English", result
    assert result["translated"] == "Traduzido", result
    assert result["languages"] == expected_languages, result

    # The compact bottom strip is always ordered Appearance, Language, Help (no Interface choice since 2026-10-10).
    ordered = [
        "button('appearance'",
        "button('language'",
        "button('help'",
    ]
    positions = [settings.find(marker) for marker in ordered]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        raise AssertionError(f"Settings order mismatch: {positions}")
    require(settings, "SUITE_LANGUAGE_KEY='inkdos2:language'", "Legacy suite language migration source")
    # Owner decision (2026-10-19): English is built in and one downloaded language package serves the whole suite,
    # so every workspace shares the suite language key and every choice goes through the package notice.
    require(settings, "function languageKey(){return SUITE_LANGUAGE_KEY}", "Suite-wide language persistence")
    require(settings, "api.chooseLanguage(language.code", "Language package notice in workspaces")
    if "api.setLanguage(" in settings:
        raise AssertionError("Workspaces must switch language through chooseLanguage (the package notice)")
    require((ROOT / "shared/localization/home-settings.js").read_text(encoding="utf-8"), "api.chooseLanguage(language.code", "Language package notice on Home")
    for marker in ("Getting started", "Keyboard shortcuts", "File compatibility", "Check for updates", "About InkDOS"):
        require(settings, marker, "Compact Help menu")

    # Density is always the desktop density (no stored choice); the module keeps its workspace-scoped key names in its API.
    require(density, "SUITE_STORAGE_KEY='inkdos2:ui-density'", "Suite density key name")
    require(density, "STORAGE_KEY=WORKSPACE?'inkdos2:'+WORKSPACE+':ui-density':SUITE_STORAGE_KEY", "Workspace density key name")
    require(density, "localization/ui-localization.js", "Localization runtime bootstrap")
    require(density, "localization/settings-strip.js", "Settings strip bootstrap")
    require(density, "localization/localization.css", "Settings CSS bootstrap")

    # Every workspace already consumes ui-density.js, which is the isolated bootstrap boundary.
    entries = {
        ROOT / "apps/documents/index.html",
        ROOT / "apps/spreadsheets/index.html",
        ROOT / "apps/presentations/index.html",
        ROOT / "apps/pdf/index.html",
        ROOT / "apps/epub/index.html",
        ROOT / "apps/txt/page.template.html",
    }
    for entry in entries:
        require(entry.read_text(encoding="utf-8"), "../../shared/ui-density.js", f"Workspace bootstrap: {entry.relative_to(ROOT)}")

    # Hidden full-screen layers must never remain hit-testable during first-open bootstrap.
    for needle in (".backdrop[hidden]", ".loading-overlay[hidden]", ".error-overlay[hidden]", "pointer-events:none!important"):
        require(css, needle, "Hidden overlay click guard")

    for needle in ("overflow-wrap", "max-inline-size", "text-overflow", "[data-settings-item]"):
        require(css, needle, "Long-label overflow guard")

    # PWA install shell contains the separated layer; locale packages are downloaded on demand, one at a time.
    sw = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    for asset in [
        '"./shared/localization/ui-localization.js"',
        '"./shared/localization/settings-strip.js"',
        '"./shared/localization/home-settings.js"',
        '"./shared/localization/localization.css"',
    ]:
        require(sw, asset, "Offline localization shell")
    shell = re.search(r"const APP_SHELL=(\[.*?\]);", sw, re.S).group(1)
    on_demand = re.search(r"const ON_DEMAND=(\[.*?\]);", sw, re.S).group(1)
    for code in LOCALES:
        asset = f'"./shared/localization/locales/{code}.js"'
        if asset in shell:
            raise AssertionError(f"Locale package {code} must not be precached")
        require(on_demand, asset, "Downloadable locale package")
    require(sw, "inkdos:drop-locales", "Switching to English removes the language package")
    require(sw, "dropLocales(cache,normalized.url)", "Only one language package on the device")

    # The notice shows each package's real size.
    sizes = json.loads(re.search(r"const PACKAGE_BYTES=Object.freeze\((\{.*?\})\);", runtime).group(1))
    for code in LOCALES:
        actual = (ROOT / f"shared/localization/locales/{code}.js").stat().st_size
        if sizes.get(code) != actual:
            raise AssertionError(f"PACKAGE_BYTES[{code}]={sizes.get(code)} but the file has {actual} bytes")

    print("InkDOS 2.4 localization/settings contract: OK")


if __name__ == "__main__":
    main()
