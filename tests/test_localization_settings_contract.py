#!/usr/bin/env python3
from __future__ import annotations

import json
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

    # The compact bottom strip is always ordered Appearance, Interface, Language, Help.
    ordered = [
        "button('appearance'",
        "button('interface'",
        "button('language'",
        "button('help'",
    ]
    positions = [settings.find(marker) for marker in ordered]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        raise AssertionError(f"Settings order mismatch: {positions}")
    require(settings, "inkdos2:'+app+':language", "App-local language persistence")
    forbid(settings, "inkdos2:language", "Language preference must not be suite-global")
    for marker in ("Getting started", "Keyboard shortcuts", "File compatibility", "Check for updates", "About InkDOS"):
        require(settings, marker, "Compact Help menu")

    # Existing density behavior is retained, but workspace persistence is independently keyed.
    require(density, "LEGACY_STORAGE_KEY='inkdos2:ui-density'", "Density migration key")
    require(density, "'inkdos2:'+WORKSPACE+':ui-density'", "App-local density persistence")
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

    for needle in ("overflow-wrap", "max-inline-size", "text-overflow", "[data-settings-item]"):
        require(css, needle, "Long-label overflow guard")

    # PWA install shell contains the separated layer and all optional locale packages.
    sw = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    for asset in [
        '"./shared/localization/ui-localization.js"',
        '"./shared/localization/settings-strip.js"',
        '"./shared/localization/localization.css"',
        *[f'"./shared/localization/locales/{code}.js"' for code in LOCALES],
    ]:
        require(sw, asset, "Offline localization shell")

    print("InkDOS 2.4 localization/settings contract: OK")


if __name__ == "__main__":
    main()
