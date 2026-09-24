#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: missing {needle!r}")


def main() -> None:
    density = read("shared/ui-density.js")
    settings = read("shared/localization/settings-strip.js")
    localization = read("shared/localization/ui-localization.js")
    home = read("index.html")
    sw = read("service-worker.js")

    require(density, "SUITE_STORAGE_KEY='inkdos2:ui-density'", "Legacy suite display preference")
    require(density, "STORAGE_KEY=WORKSPACE?'inkdos2:'+WORKSPACE+':ui-density':SUITE_STORAGE_KEY", "Workspace display preference")
    require(density, "LEGACY_SUITE_KEY=WORKSPACE?SUITE_STORAGE_KEY:null", "Display migration")
    require(settings, "SUITE_LANGUAGE_KEY='inkdos2:language'", "Legacy suite language preference")
    require(settings, "return app?'inkdos2:'+app+':language':SUITE_LANGUAGE_KEY", "Workspace language preference")
    require(settings, "legacyLanguageKey", "Language migration")
    require(settings, "[data-appearance-mode=\"'+mode+'\"]", "EPUB/TXT appearance selector parity")
    require(settings, "['mobile','Smartphone']", "Consistent display label")
    require(localization, "doc.documentElement.lang=language", "Document language synchronization")
    require(localization, "bindStorage", "Cross-window language synchronization")
    require(localization, "legacyStorageKeys", "Legacy language migration")

    # Home keeps the legacy suite keys as its own preferences; apps migrate once and then diverge.
    require(home, './shared/localization/ui-localization.js', "Home localization runtime")
    require(home, './shared/localization/home-settings.js', "Home language settings")
    require(home, 'aria-label="Settings" title="Settings"', "Home unified settings control")
    require(sw, '"./shared/localization/home-settings.js"', "Offline Home language settings")

    # Every workspace theme runtime owns its local key and uses the former suite
    # appearance key only as a one-time migration source.
    appearance_files = [
        "apps/documents/state/appearance.js",
        "apps/spreadsheets/state/appearance.js",
        "apps/presentations/state/appearance.js",
        "apps/pdf/state/appearance.js",
        "apps/epub/state/appearance.js",
        "apps/txt/state/appearance.js",
    ]
    for rel in appearance_files:
        text = read(rel)
        require(text, "LEGACY_SUITE_KEY='inkdos2:appearance'", f"Legacy appearance migration: {rel}")
        require(text, "dataset.theme", f"Common resolved theme marker: {rel}")
        if "setItem(LEGACY_SUITE_KEY" in text:
            raise AssertionError(f"Workspace must not publish appearance back to suite key: {rel}")

    first_paint = {
        "apps/epub/index.html": 'var k="inkdos2:epub:appearance",l="inkdos2:appearance"',
        "apps/txt/page.template.html": 'var k="inkdos2:txt:appearance",l="inkdos2:appearance"',
    }
    for rel, marker in first_paint.items():
        text = read(rel)
        require(text, marker, f"Workspace-first appearance migration: {rel}")

    # Locale packages stay key-identical and include the Home shell terminology.
    locale_dir = ROOT / "shared/localization/locales"
    for path in locale_dir.glob("*.js"):
        text = path.read_text(encoding="utf-8")
        for key in ("Smartphone", "Choose a workspace", "Local-first workspace", "Project links"):
            require(text, f"'{key}':", f"Home/settings locale key {path.name}")

    print("InkDOS suite settings concordance contract: OK")


if __name__ == "__main__":
    main()
