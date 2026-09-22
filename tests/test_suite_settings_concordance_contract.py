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

    require(density, "SUITE_STORAGE_KEY='inkdos2:ui-density'", "Suite display preference")
    require(density, "LEGACY_WORKSPACE_KEY", "Display migration")
    require(settings, "LANGUAGE_KEY='inkdos2:language'", "Suite language preference")
    require(settings, "legacyLanguageKey", "Language migration")
    require(settings, "[data-appearance-mode=\"'+mode+'\"]", "EPUB/TXT appearance selector parity")
    require(settings, "['mobile','Smartphone']", "Consistent display label")
    require(localization, "doc.documentElement.lang=language", "Document language synchronization")
    require(localization, "bindStorage", "Cross-window language synchronization")
    require(localization, "legacyStorageKeys", "Legacy language migration")

    # Home participates in all three suite preferences.
    require(home, './shared/localization/ui-localization.js', "Home localization runtime")
    require(home, './shared/localization/home-settings.js', "Home language settings")
    require(home, 'aria-label="Settings" title="Settings"', "Home unified settings control")
    require(sw, '"./shared/localization/home-settings.js"', "Offline Home language settings")

    # Every workspace theme runtime consumes the suite appearance key and exposes
    # a common resolved theme dataset without removing its existing CSS contract.
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
        require(text, "inkdos2:appearance", f"Suite appearance key: {rel}")
        require(text, "dataset.theme", f"Common resolved theme marker: {rel}")

    for rel in ("apps/epub/index.html", "apps/txt/page.template.html"):
        text = read(rel)
        require(text, 'localStorage.getItem("inkdos2:appearance")', f"First-paint suite theme: {rel}")

    # Locale packages stay key-identical and include the Home shell terminology.
    locale_dir = ROOT / "shared/localization/locales"
    for path in locale_dir.glob("*.js"):
        text = path.read_text(encoding="utf-8")
        for key in ("Smartphone", "Choose a workspace", "Local-first workspace", "Project links"):
            require(text, f"'{key}':", f"Home/settings locale key {path.name}")

    print("InkDOS suite settings concordance contract: OK")


if __name__ == "__main__":
    main()
