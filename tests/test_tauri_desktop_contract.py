import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"
TAURI = DESKTOP / "src-tauri"
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-tauri.yml"


def read(path: Path) -> str:
    assert path.exists(), f"required desktop file is missing: {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_tauri_shell_configuration_matches_inkdos_release():
    version = json.loads(read(ROOT / "VERSION.json"))["version"]
    config = json.loads(read(TAURI / "tauri.conf.json"))
    assert config["productName"] == "InkDOS"
    assert config["version"] == version == "2.1.0"
    assert config["identifier"] == "com.inkdos.desktop"
    assert config["build"]["frontendDist"] == "../web-dist"
    assert config["app"]["withGlobalTauri"] is True
    assert config["app"]["windows"][0]["label"] == "main"


def test_tauri_rust_dependencies_are_v2_and_node_free():
    cargo = read(TAURI / "Cargo.toml")
    assert 'tauri = { version = "2"' in cargo
    assert 'tauri-plugin-dialog = "2"' in cargo
    assert 'tauri-plugin-fs = "2"' in cargo
    assert 'tauri-plugin-opener = "2"' in cargo
    lowered = cargo.lower()
    assert "electron" not in lowered
    assert "node" not in lowered


def test_capability_is_explicit_and_has_no_broad_static_filesystem_scope():
    capability = json.loads(read(TAURI / "capabilities" / "default.json"))
    assert capability["windows"] == ["main"]
    permissions = capability["permissions"]
    required = {
        "core:default",
        "dialog:allow-open",
        "dialog:allow-save",
        "fs:allow-read-file",
        "fs:allow-write-file",
        "opener:allow-default-urls",
    }
    assert required.issubset(set(permissions))
    assert all(not isinstance(item, dict) or item.get("identifier") != "fs:scope" for item in permissions)
    assert "shell:allow-execute" not in permissions
    assert "shell:allow-spawn" not in permissions


def test_desktop_bridge_maps_native_open_save_and_external_links():
    bridge = read(DESKTOP / "desktop-host.js")
    for marker in (
        "window.__TAURI__",
        "dialog.save",
        "fs.writeFile",
        "dialog.open",
        "fs.readFile",
        "showSaveFilePicker",
        "DataTransfer",
        "opener.openUrl",
        "deliveryConfirmed",
    ):
        assert marker in bridge


def test_stager_injects_bridge_without_editing_source_html():
    stager = read(DESKTOP / "scripts" / "stage_web.py")
    assert "desktop-host.js" in stager
    assert "<head>" in stager
    assert "web-dist" in stager
    assert "service-worker.js" in stager
    assert "apps" in stager
    assert "assets" in stager
    assert "--check" in stager


def test_native_build_workflow_targets_all_desktop_platforms_without_node():
    workflow = read(WORKFLOW)
    for marker in (
        "desktop-tauri",
        "windows-latest",
        "macos-latest",
        "ubuntu-22.04",
        "cargo tauri build",
        "InkDOS-Windows",
        "InkDOS-macOS",
        "InkDOS-Linux",
        "libwebkit2gtk-4.1-dev",
        "python desktop/scripts/stage_web.py",
    ):
        assert marker in workflow
    assert "setup-node" not in workflow
    assert "npm install" not in workflow
    assert "npm run" not in workflow


def test_bundle_targets_cover_expected_installers():
    config = json.loads(read(TAURI / "tauri.conf.json"))
    targets = set(config["bundle"]["targets"])
    assert {"nsis", "msi", "app", "dmg", "deb", "appimage", "rpm"}.issubset(targets)


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"desktop contract: {len(tests)} checks passed")
