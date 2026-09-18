import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALE_DIR = ROOT / "shared" / "localization" / "locales"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def locale_keys(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    marker = "translations:Object.freeze({"
    assert marker in text, path
    body = text.split(marker, 1)[1].rsplit("})", 2)[0]
    return {key for key, _ in re.findall(r"'((?:\\'|[^'])*)':'((?:\\'|[^'])*)'", body)}


def test_release_version_is_consistent_across_desktop_metadata():
    metadata = json.loads(read("VERSION.json"))
    version = metadata["version"]
    assert metadata["releaseName"] == f"InkDOS {version}"
    tauri = json.loads(read("desktop/src-tauri/tauri.conf.json"))["version"]
    cargo = read("desktop/src-tauri/Cargo.toml")
    package = cargo.split("[package]", 1)[1].split("[build-dependencies]", 1)[0]
    match = re.search(r'^version\s*=\s*"([^"]+)"', package, re.M)
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert tauri == version
    assert match and match.group(1) == version


def test_home_has_no_visible_version_badge():
    home = read("index.html")
    css = read("assets/home.css")
    assert '<div class="version">' not in home
    assert not re.search(r"<span>InkDOS\s+\d+\.\d+\.\d+</span>", home)
    assert ".status-dot{" not in css
    assert ".version{" not in css


def test_localization_covers_safe_document_chrome_and_locale_keys_match():
    runtime = read("shared/localization/ui-localization.js")
    assert ".context-drawer .drawer-head" in runtime
    assert ".context-drawer .sidebar-tabs" in runtime
    assert "parent.closest('#contextDrawer,.context-drawer" not in runtime

    locale_files = sorted(LOCALE_DIR.glob("*.js"))
    assert locale_files
    keysets = {path.name: locale_keys(path) for path in locale_files}
    reference = next(iter(keysets.values()))
    for name, keys in keysets.items():
        assert keys == reference, f"locale key mismatch: {name}"
        assert "Document" in keys
        assert {"Pages", "Outline", "Search"}.issubset(keys)
        assert {"InkDOS update", "Installed", "Latest", "Install", "Cancel"}.issubset(keys)


def test_transient_toolbar_panels_use_one_exclusive_channel():
    frame = read("apps/documents/runtime/frame/frame-menu.js")
    settings = read("shared/localization/settings-strip.js")
    commands = read("apps/documents/ui/command-controller.js")
    for source in (frame, settings):
        assert "inkdos:transient-open" in source
        assert "dispatchEvent" in source
        assert "addEventListener" in source
    assert "close({restoreFocus:false})" in frame
    assert "closePopover" in settings
    assert "closeToolbarTransientExcept" in commands


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"InkDOS desktop UX contract: {len(tests)} checks passed")
